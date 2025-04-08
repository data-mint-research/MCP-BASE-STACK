"""
SQLAlchemy models for MCP persistence.

This module defines the database models for all MCP entities, including
servers, clients, tools, resources, subscriptions, sessions, and consent records.
"""

import enum
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Text, DateTime, 
    ForeignKey, Enum, JSON, LargeBinary, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ConsentLevelEnum(enum.Enum):
    """Consent levels for operations."""
    NONE = 0
    READ_ONLY = 1
    BASIC = 2
    ELEVATED = 3
    FULL = 4


class RoleEnum(enum.Enum):
    """User roles for role-based access control."""
    USER = 1
    POWER_USER = 2
    ADMIN = 3


class Server(Base):
    """Model for MCP Server entities."""
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True)
    server_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    description = Column(String(1024), nullable=True)
    version = Column(String(50), nullable=True)
    capabilities = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tools = relationship("Tool", back_populates="server", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="server", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="server", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="server", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "server_id": self.server_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Server':
        """Create model from dictionary."""
        return cls(
            server_id=data.get("server_id"),
            name=data.get("name"),
            description=data.get("description"),
            version=data.get("version"),
            capabilities=data.get("capabilities", {})
        )


class Client(Base):
    """Model for MCP Client entities."""
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    capabilities = Column(JSON, nullable=False, default=dict)
    context = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="client", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="client", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="client", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "client_id": self.client_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        """Create model from dictionary."""
        return cls(
            client_id=data.get("client_id"),
            name=data.get("name"),
            capabilities=data.get("capabilities", {}),
            context=data.get("context", {})
        )


class Tool(Base):
    """Model for MCP Tool entities."""
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    input_schema = Column(JSON, nullable=False, default=dict)
    dangerous = Column(Boolean, default=False)
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    server = relationship("Server", back_populates="tools")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('server_id', 'name', name='uix_tool_server_name'),
        Index('ix_tool_name', 'name'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "dangerous": self.dangerous,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], server_id: int) -> 'Tool':
        """Create model from dictionary."""
        return cls(
            server_id=server_id,
            name=data.get("name"),
            description=data.get("description"),
            input_schema=data.get("input_schema", {}),
            dangerous=data.get("dangerous", False),
            metadata=data.get("metadata", {})
        )


class Resource(Base):
    """Model for MCP Resource entities."""
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    uri = Column(String(1024), nullable=False, index=True)
    provider = Column(String(255), nullable=False)
    metadata = Column(JSON, nullable=False, default=dict)
    cache_key = Column(String(255), nullable=True, index=True)
    cache_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # For caching resource content (optional)
    content = Column(LargeBinary, nullable=True)
    content_type = Column(String(255), nullable=True)
    
    # Relationships
    server = relationship("Server", back_populates="resources")
    subscriptions = relationship("Subscription", back_populates="resource", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('server_id', 'uri', name='uix_resource_server_uri'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "uri": self.uri,
            "provider": self.provider,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], server_id: int) -> 'Resource':
        """Create model from dictionary."""
        return cls(
            server_id=server_id,
            uri=data.get("uri"),
            provider=data.get("provider"),
            metadata=data.get("metadata", {})
        )


class Subscription(Base):
    """Model for MCP Resource Subscription entities."""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(String(255), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    callback_id = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_notification = Column(DateTime, nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="subscriptions")
    server = relationship("Server", back_populates="subscriptions")
    resource = relationship("Resource", back_populates="subscriptions")
    
    # Indexes
    __table_args__ = (
        Index('ix_subscription_client_resource', 'client_id', 'resource_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "subscription_id": self.subscription_id,
            "callback_id": self.callback_id,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_notification": self.last_notification.isoformat() if self.last_notification else None
        }


class Session(Base):
    """Model for MCP User Session entities."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(255), nullable=False)
    token = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.USER)
    permissions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expiration = Column(DateTime, nullable=False)
    
    # Relationships
    client = relationship("Client", back_populates="sessions")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "session_id": self.session_id,
            "username": self.username,
            "role": self.role.name if self.role else None,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "expiration": self.expiration.isoformat() if self.expiration else None
        }


class Consent(Base):
    """Model for MCP Consent records."""
    __tablename__ = "consents"
    
    id = Column(Integer, primary_key=True)
    consent_id = Column(String(255), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    operation_pattern = Column(String(255), nullable=False)
    consent_level = Column(Enum(ConsentLevelEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    expiration = Column(DateTime, nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="consents")
    server = relationship("Server", back_populates="consents")
    
    # Indexes
    __table_args__ = (
        Index('ix_consent_client_server', 'client_id', 'server_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "consent_id": self.consent_id,
            "operation_pattern": self.operation_pattern,
            "consent_level": self.consent_level.name if self.consent_level else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "expiration": self.expiration.isoformat() if self.expiration else None
        }