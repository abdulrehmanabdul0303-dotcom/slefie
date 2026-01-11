"""
Celery tasks for image processing.
"""
from celery import shared_task
from django.utils import timezone
from PIL import Image as PILImage
import os
import tempfile
from .models import Image, ImageProcessingJob, FaceDetection


@shared_task
def generate_thumbnail_task(image_id, job_id):
    """
    Generate thumbnail for an image.
    """
    from .services import ImageService, StorageService
    
    try:
        job = ImageProcessingJob.objects.get(id=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()
        
        image = Image.objects.get(id=image_id)
        
        # Get original image data
        image_data = StorageService.get_image_file(image.storage_key, image.user)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(image_data)
            temp_path = temp_file.name
        
        try:
            # Generate thumbnail
            pil_image = PILImage.open(temp_path)
            pil_image.thumbnail((300, 300), PILImage.Resampling.LANCZOS)
            
            # Save thumbnail
            thumb_temp_path = temp_path + '_thumb.jpg'
            pil_image.save(thumb_temp_path, 'JPEG', quality=85)
            
            # Read thumbnail data
            with open(thumb_temp_path, 'rb') as f:
                thumb_data = f.read()
            
            # Encrypt and store thumbnail
            encrypted_thumb = StorageService.encrypt_file(thumb_data, image.user)
            thumb_storage_key = image.storage_key.replace('.enc', '_thumb.enc')
            StorageService.save_file(thumb_storage_key, encrypted_thumb)
            
            # Update image record
            image.thumb_storage_key = thumb_storage_key
            image.save()
            
            # Clean up
            os.unlink(thumb_temp_path)
            
        finally:
            os.unlink(temp_path)
        
        # Mark job as completed
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save()
        
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()


@shared_task
def extract_exif_task(image_id, job_id):
    """
    Extract EXIF data from an image.
    """
    from .services import ImageService, StorageService
    try:
        job = ImageProcessingJob.objects.get(id=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()
        
        image = Image.objects.get(id=image_id)
        
        # Get original image data
        image_data = StorageService.get_image_file(image.storage_key, image.user)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(image_data)
            temp_path = temp_file.name
        
        try:
            # Extract EXIF data
            exif_data = ImageService.extract_exif_data(temp_path)
            
            # Calculate perceptual hash
            phash = ImageService.calculate_perceptual_hash(temp_path)
            
            # Update image record
            image.exif_data = exif_data
            image.phash_hex = phash
            
            # Extract camera info
            if 'Make' in exif_data:
                image.camera_make = exif_data['Make']
            if 'Model' in exif_data:
                image.camera_model = exif_data['Model']
            
            # Extract GPS coordinates
            if 'GPSInfo' in exif_data:
                # TODO: Parse GPS coordinates from EXIF
                pass
            
            # Extract date taken
            if 'DateTime' in exif_data:
                try:
                    from datetime import datetime
                    image.taken_at = datetime.strptime(exif_data['DateTime'], '%Y:%m:%d %H:%M:%S')
                except:
                    pass
            
            image.save()
            
        finally:
            os.unlink(temp_path)
        
        # Mark job as completed
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.result_data = {'exif_fields_extracted': len(exif_data)}
        job.save()
        
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()


@shared_task
def detect_faces_task(image_id, job_id):
    """
    Detect faces in an image.
    """
    from .services import ImageService, StorageService
    
    try:
        job = ImageProcessingJob.objects.get(id=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()
        
        image = Image.objects.get(id=image_id)
        
        # Get original image data
        image_data = StorageService.get_image_file(image.storage_key, image.user)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(image_data)
            temp_path = temp_file.name
        
        try:
            # Implement face detection using face_recognition library
            import face_recognition
            import numpy as np
            
            # Load image for face detection
            image_array = face_recognition.load_image_file(temp_path)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(image_array)
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            
            faces_detected = []
            
            for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                # Convert face location to normalized coordinates
                top, right, bottom, left = face_location
                height, width = image_array.shape[:2]
                
                bbox_x = left / width
                bbox_y = top / height
                bbox_width = (right - left) / width
                bbox_height = (bottom - top) / height
                
                # Create face detection record
                face_detection = FaceDetection.objects.create(
                    image=image,
                    bbox_x=bbox_x,
                    bbox_y=bbox_y,
                    bbox_width=bbox_width,
                    bbox_height=bbox_height,
                    face_embedding_json=face_encoding.tolist(),  # Real 128-dimensional encoding
                    confidence=0.95,  # face_recognition doesn't provide confidence, use default
                    face_id=f"face_{image.id}_{i+1}"
                )
                faces_detected.append(face_detection)
            
            # If no faces detected, that's fine - just log it
            if not faces_detected:
                job.status = 'completed'
                job.result_data = {'faces_count': 0, 'message': 'No faces detected'}
            else:
                job.status = 'completed'
                job.result_data = {'faces_count': len(faces_detected)}
                
        except ImportError:
            # face_recognition not available, use OpenCV fallback
            import cv2
            
            # Load OpenCV face cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Read image
            img = cv2.imread(temp_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            faces_detected = []
            height, width = img.shape[:2]
            
            for i, (x, y, w, h) in enumerate(faces):
                # Convert to normalized coordinates
                bbox_x = x / width
                bbox_y = y / height
                bbox_width = w / width
                bbox_height = h / height
                
                # Create face detection record (no embedding with OpenCV)
                face_detection = FaceDetection.objects.create(
                    image=image,
                    bbox_x=bbox_x,
                    bbox_y=bbox_y,
                    bbox_width=bbox_width,
                    bbox_height=bbox_height,
                    face_embedding_json=[0.0] * 128,  # Placeholder embedding
                    confidence=0.8,  # Lower confidence for OpenCV
                    face_id=f"face_{image.id}_{i+1}"
                )
                faces_detected.append(face_detection)
            
            job.status = 'completed'
            job.result_data = {'faces_count': len(faces_detected), 'method': 'opencv_fallback'}
            
        finally:
            os.unlink(temp_path)
        
        # Mark job as completed
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.result_data = {'faces_detected': len(faces_detected)}
        job.save()
        
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()


@shared_task
def generate_embedding_task(image_id, job_id):
    """
    Generate CLIP embedding for semantic search.
    """
    from .services import ImageService, StorageService
    
    try:
        job = ImageProcessingJob.objects.get(id=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()
        
        image = Image.objects.get(id=image_id)
        
        # Get original image data
        image_data = StorageService.get_image_file(image.storage_key, image.user)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(image_data)
            temp_path = temp_file.name
        
        try:
            # Generate embedding
            from .services import EmbeddingService
            embedding = EmbeddingService.generate_clip_embedding(temp_path)
            
            # Update image record
            image.embedding_json = embedding
            image.save()
            
        finally:
            os.unlink(temp_path)
        
        # Mark job as completed
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.result_data = {'embedding_dimensions': len(embedding) if embedding else 0}
        job.save()
        
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()