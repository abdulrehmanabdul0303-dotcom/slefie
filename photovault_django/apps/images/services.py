"""
Services for image processing and management.
"""
import os
import hashlib
import json
from PIL import Image as PILImage
from PIL.ExifTags import TAGS
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q
from cryptography.fernet import Fernet
import imagehash
from datetime import datetime

from .models import Image, ImageProcessingJob
from .tasks import (
    generate_thumbnail_task,
    extract_exif_task,
    detect_faces_task,
    generate_embedding_task,
)


class ImageService:
    """
    Service for image processing and management.
    """
    
    @staticmethod
    def process_upload(user, file, folder=None):
        """
        Process uploaded image file.
        """
        # Calculate SHA256 checksum
        file.seek(0)
        checksum = hashlib.sha256(file.read()).hexdigest()
        file.seek(0)
        
        # Check for duplicates
        existing_image = Image.objects.filter(
            user=user,
            checksum_sha256=checksum
        ).first()
        
        if existing_image:
            raise ValueError("Duplicate image already exists")
        
        # Open image to get dimensions and basic info
        pil_image = PILImage.open(file)
        width, height = pil_image.size
        
        # Generate storage key
        storage_key = f"users/{user.id}/images/{checksum[:2]}/{checksum}.enc"
        
        # Encrypt and store file
        encrypted_data = StorageService.encrypt_file(file.read(), user)
        StorageService.save_file(storage_key, encrypted_data)
        
        # Create image record
        image = Image.objects.create(
            user=user,
            folder=folder,
            original_filename=file.name,
            content_type=file.content_type,
            size_bytes=file.size,
            width=width,
            height=height,
            storage_key=storage_key,
            checksum_sha256=checksum,
        )
        
        return image
    
    @staticmethod
    def start_background_processing(image):
        """
        Start background processing tasks for an image.
        """
        # Generate thumbnail
        job = ImageProcessingJob.objects.create(
            image=image,
            job_type='thumbnail',
            status='pending'
        )
        generate_thumbnail_task.delay(image.id, job.id)
        
        # Extract EXIF data
        job = ImageProcessingJob.objects.create(
            image=image,
            job_type='exif_extraction',
            status='pending'
        )
        extract_exif_task.delay(image.id, job.id)
        
        # Detect faces
        job = ImageProcessingJob.objects.create(
            image=image,
            job_type='face_detection',
            status='pending'
        )
        detect_faces_task.delay(image.id, job.id)
        
        # Generate embeddings
        job = ImageProcessingJob.objects.create(
            image=image,
            job_type='embedding',
            status='pending'
        )
        generate_embedding_task.delay(image.id, job.id)
    
    @staticmethod
    def search_images(user, search_params):
        """
        Search images based on various criteria.
        """
        queryset = Image.objects.filter(user=user)
        
        # Text search in filename and tags
        query = search_params.get('query')
        if query:
            queryset = queryset.filter(
                Q(original_filename__icontains=query) |
                Q(tags__tag__icontains=query) |
                Q(location_text__icontains=query)
            ).distinct()
        
        # Folder filter
        folder = search_params.get('folder')
        if folder:
            queryset = queryset.filter(folder_id=folder)
        
        # Tag filter
        tags = search_params.get('tags')
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__tag__iexact=tag)
        
        # Date range filter
        date_from = search_params.get('date_from')
        date_to = search_params.get('date_to')
        if date_from:
            queryset = queryset.filter(taken_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(taken_at__lte=date_to)
        
        # Location filter
        has_location = search_params.get('has_location')
        if has_location is True:
            queryset = queryset.filter(gps_lat__isnull=False, gps_lng__isnull=False)
        elif has_location is False:
            queryset = queryset.filter(Q(gps_lat__isnull=True) | Q(gps_lng__isnull=True))
        
        # Face filter
        has_faces = search_params.get('has_faces')
        if has_faces is True:
            queryset = queryset.filter(faces__isnull=False).distinct()
        elif has_faces is False:
            queryset = queryset.filter(faces__isnull=True)
        
        # Camera filter
        camera_make = search_params.get('camera_make')
        if camera_make:
            queryset = queryset.filter(camera_make__icontains=camera_make)
        
        camera_model = search_params.get('camera_model')
        if camera_model:
            queryset = queryset.filter(camera_model__icontains=camera_model)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def extract_exif_data(image_path):
        """
        Extract EXIF data from image.
        """
        try:
            pil_image = PILImage.open(image_path)
            exif_data = {}
            
            if hasattr(pil_image, '_getexif'):
                exif = pil_image._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_data[tag] = str(value)
            
            return exif_data
        except Exception:
            return {}
    
    @staticmethod
    def calculate_perceptual_hash(image_path):
        """
        Calculate perceptual hash for duplicate detection.
        """
        try:
            pil_image = PILImage.open(image_path)
            phash = imagehash.phash(pil_image)
            return str(phash)
        except Exception:
            return None


class StorageService:
    """
    Service for encrypted file storage.
    """
    
    @staticmethod
    def _get_user_encryption_key(user):
        """
        Get or derive encryption key for user.
        """
        # Use user's DEK if available, otherwise derive from settings
        if user.dek_encrypted_b64 and user.dek_encrypted_b64 != 'placeholder_dek':
            # In production, this would decrypt the user's DEK with their password
            # For now, use a derived key based on user ID and settings key
            base_key = settings.PHOTOVAULT_ENCRYPTION_KEY or settings.SECRET_KEY
            user_salt = f"user_{user.id}_{user.date_joined.isoformat()}"
            combined = f"{base_key}_{user_salt}".encode()
            key = hashlib.sha256(combined).digest()
            return Fernet(Fernet.generate_key())  # Use proper key derivation
        else:
            # Fallback to settings-based key
            base_key = settings.PHOTOVAULT_ENCRYPTION_KEY or settings.SECRET_KEY
            key = hashlib.sha256(base_key.encode()).digest()[:32]
            # Pad to 32 bytes and base64 encode for Fernet
            import base64
            fernet_key = base64.urlsafe_b64encode(key)
            return Fernet(fernet_key)
    
    @staticmethod
    def encrypt_file(file_data, user):
        """
        Encrypt file data with user's DEK.
        """
        try:
            fernet = StorageService._get_user_encryption_key(user)
            return fernet.encrypt(file_data)
        except Exception as e:
            # Log error but don't expose details
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"File encryption failed for user {user.id}: {e}")
            # In production, this should fail securely
            raise ValueError("File encryption failed")
    
    @staticmethod
    def decrypt_file(encrypted_data, user):
        """
        Decrypt file data with user's DEK.
        """
        try:
            fernet = StorageService._get_user_encryption_key(user)
            return fernet.decrypt(encrypted_data)
        except Exception as e:
            # Log error but don't expose details
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"File decryption failed for user {user.id}: {e}")
            # In production, this should fail securely
            raise ValueError("File decryption failed")
    
    @staticmethod
    def save_file(storage_key, data):
        """
        Save file to storage.
        """
        # Ensure directory exists
        directory = os.path.dirname(storage_key)
        full_directory = os.path.join(settings.MEDIA_ROOT, directory)
        os.makedirs(full_directory, exist_ok=True)
        
        # Save file
        full_path = os.path.join(settings.MEDIA_ROOT, storage_key)
        with open(full_path, 'wb') as f:
            f.write(data)
    
    @staticmethod
    def get_image_file(storage_key, user):
        """
        Get and decrypt image file.
        """
        full_path = os.path.join(settings.MEDIA_ROOT, storage_key)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError("Image file not found")
        
        with open(full_path, 'rb') as f:
            encrypted_data = f.read()
        
        return StorageService.decrypt_file(encrypted_data, user)
    
    @staticmethod
    def delete_image_files(image):
        """
        Delete image files from storage.
        """
        # Delete main image file
        if image.storage_key:
            full_path = os.path.join(settings.MEDIA_ROOT, image.storage_key)
            if os.path.exists(full_path):
                os.remove(full_path)
        
        # Delete thumbnail file
        if image.thumb_storage_key:
            full_path = os.path.join(settings.MEDIA_ROOT, image.thumb_storage_key)
            if os.path.exists(full_path):
                os.remove(full_path)


class EmbeddingService:
    """
    Service for generating and managing embeddings.
    """
    
    @staticmethod
    def generate_clip_embedding(image_path):
        """
        Generate CLIP embedding for semantic search.
        """
        # TODO: Implement CLIP embedding generation
        # This would use a model like OpenAI's CLIP or similar
        # For now, return a placeholder
        return [0.0] * 512  # 512-dimensional embedding
    
    @staticmethod
    def search_by_embedding(user, query_embedding, limit=20):
        """
        Search images by embedding similarity.
        """
        # TODO: Implement vector similarity search
        # This would use cosine similarity or similar metric
        # For now, return empty results
        return Image.objects.filter(user=user)[:limit]