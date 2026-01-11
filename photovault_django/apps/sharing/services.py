"""
Services for sharing system.
"""
import numpy as np
from PIL import Image
import io
import json


class FaceVerificationService:
    """
    Service for face verification in sharing system.
    """
    
    @staticmethod
    def extract_face_embedding(image_file):
        """
        Extract face embedding from uploaded image.
        
        Args:
            image_file: Django UploadedFile object
            
        Returns:
            list: Face embedding vector or None if no face detected
        """
        try:
            # TODO: Implement actual face detection and embedding extraction
            # This is a placeholder implementation
            
            # Open image
            image = Image.open(image_file)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Implement real face extraction using face_recognition
            try:
                import face_recognition
                import numpy as np
                
                # Convert PIL image to numpy array
                image_array = np.array(image)
                
                # Find face encodings
                face_encodings = face_recognition.face_encodings(image_array)
                
                if face_encodings:
                    # Return the first face encoding found
                    return face_encodings[0].tolist()
                else:
                    # No face found
                    return None
                    
            except ImportError:
                # Fallback: use OpenCV for face detection (no encoding)
                import cv2
                import numpy as np
                
                # Convert PIL to OpenCV format
                image_array = np.array(image)
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
                
                # Load face cascade
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                
                # Detect faces
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    # Return a placeholder embedding if face detected
                    return [0.0] * 128  # Placeholder embedding
                else:
                    return None
            
        except Exception as e:
            print(f"Face extraction error: {e}")
            return None
    
    @staticmethod
    def verify_face_against_album(face_embedding, album):
        """
        Verify face embedding against faces in album.
        
        Args:
            face_embedding: Face embedding to verify
            album: Album object to check against
            
        Returns:
            dict: Verification result with match status and confidence
        """
        try:
            # TODO: Implement actual face matching
            # This is a placeholder implementation
            
            from apps.images.models import FaceDetection
            
            # Get all face detections in the album
            album_faces = FaceDetection.objects.filter(
                image__albums=album
            ).exclude(face_embedding_json__isnull=True)
            
            if not album_faces.exists():
                return {
                    'match': False,
                    'confidence': 0.0,
                    'message': 'No faces found in album for comparison'
                }
            
            best_match_confidence = 0.0
            best_match_face_id = None
            
            # Compare against each face in the album
            for face_detection in album_faces:
                try:
                    stored_embedding = face_detection.face_embedding
                    if not stored_embedding:
                        continue
                    
                    # Calculate face distance using face_recognition method
                    try:
                        import face_recognition
                        # face_recognition uses Euclidean distance
                        distance = face_recognition.face_distance([stored_embedding], face_embedding)[0]
                        # Convert distance to confidence (lower distance = higher confidence)
                        confidence = max(0.0, 1.0 - distance)
                    except ImportError:
                        # Fallback to cosine similarity
                        confidence = FaceVerificationService.calculate_similarity(
                            face_embedding, 
                            stored_embedding
                        )
                    
                    if confidence > best_match_confidence:
                        best_match_confidence = confidence
                        best_match_face_id = face_detection.face_id
                        
                except Exception as e:
                    continue
            
            # Threshold for face match (configurable)
            threshold = 0.7
            is_match = best_match_confidence >= threshold
            
            return {
                'match': is_match,
                'confidence': best_match_confidence,
                'face_id': best_match_face_id,
                'threshold': threshold
            }
            
        except Exception as e:
            print(f"Face verification error: {e}")
            return {
                'match': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    @staticmethod
    def calculate_similarity(embedding1, embedding2):
        """
        Calculate cosine similarity between two face embeddings.
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            
        Returns:
            float: Similarity score (0-1)
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Convert to 0-1 range
            similarity = (similarity + 1) / 2
            
            return float(similarity)
            
        except Exception as e:
            print(f"Similarity calculation error: {e}")
            return 0.0


class ShareLinkService:
    """
    Service for managing share links.
    """
    
    @staticmethod
    def generate_qr_code(share_url):
        """
        Generate QR code for share URL.
        
        Args:
            share_url: URL to encode in QR code
            
        Returns:
            bytes: QR code image data
        """
        try:
            import qrcode
            from io import BytesIO
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(share_url)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            print(f"QR code generation error: {e}")
            return None
    
    @staticmethod
    def validate_share_access(share, request):
        """
        Validate if share can be accessed from this request.
        
        Args:
            share: PublicShare object
            request: Django request object
            
        Returns:
            dict: Validation result
        """
        # Check if share is valid
        if not share.is_valid:
            return {
                'valid': False,
                'reason': 'Share link expired or revoked'
            }
        
        # Check IP restrictions
        if share.ip_lock:
            client_ip = ShareLinkService.get_client_ip(request)
            if client_ip != share.ip_lock:
                return {
                    'valid': False,
                    'reason': 'Access restricted to specific IP address'
                }
        
        # Check user agent restrictions
        if share.user_agent_lock:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if user_agent != share.user_agent_lock:
                return {
                    'valid': False,
                    'reason': 'Access restricted to specific device'
                }
        
        return {
            'valid': True,
            'reason': 'Access granted'
        }
    
    @staticmethod
    def get_client_ip(request):
        """
        Get client IP address from request.
        
        Args:
            request: Django request object
            
        Returns:
            str: Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip