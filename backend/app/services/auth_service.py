from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.database import User, Company, UserRole
from app.models.schemas import UserRegister, UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token


logger = logging.getLogger(__name__)


class AuthService:
    """Handle authentication and user management."""
    
    
    def register_company_and_admin(
        self,
        user_data: UserRegister,
        db: Session
    ) -> tuple[User, str]:
        """
        Register a new company with an admin user.
        
        Args:
            user_data: Registration data
            db: Database session
            
        Returns:
            Tuple of (User, access_token)
        """
        try:
            # Check if email already exists
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise ValueError("Email already registered")
            
            # Check if company name already exists
            existing_company = db.query(Company).filter(Company.name == user_data.company_name).first()
            if existing_company:
                raise ValueError("Company name already taken")
            
            # Create company
            company = Company(name=user_data.company_name)
            db.add(company)
            db.flush()  # Get company ID
            
            # Create vector store collection for company
            self.vector_store.create_collection(company.id)
            
            # Create admin user
            hashed_password = get_password_hash(user_data.password)
            user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                role=UserRole.ADMIN,
                company_id=company.id,
                last_login=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Generate access token
            access_token = create_access_token(
                data={
                    "user_id": user.id,
                    "email": user.email,
                    "company_id": user.company_id,
                    "role": user.role.value
                }
            )
            
            logger.info(f"Registered new company '{company.name}' with admin user {user.email}")
            
            return user, access_token
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error during registration: {str(e)}")
            raise
    
    def create_employee(
        self,
        user_data: UserCreate,
        company_id: int,
        db: Session
    ) -> User:
        """
        Create an employee user (admin only).
        
        Args:
            user_data: User creation data
            company_id: Company ID
            db: Database session
            
        Returns:
            Created user
        """
        try:
            # Check if email already exists
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise ValueError("Email already registered")
            
            # Create user
            hashed_password = get_password_hash(user_data.password)
            user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                role=user_data.role,
                company_id=company_id
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created new user {user.email} for company {company_id}")
            
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    def authenticate_user(self, email: str, password: str, db: Session) -> tuple[User, str]:
        """
        Authenticate user and return user with access token.
        
        Args:
            email: User email
            password: User password
            db: Database session
            
        Returns:
            Tuple of (User, access_token)
        """
        # Find user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise ValueError("Invalid credentials")
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is inactive")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Generate access token
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "company_id": user.company_id,
                "role": user.role.value
            }
        )
        
        logger.info(f"User {user.email} authenticated successfully")
        
        return user, access_token
    
    def get_company_users(self, company_id: int, db: Session) -> list[User]:
        """Get all users for a company."""
        return db.query(User).filter(User.company_id == company_id).all()