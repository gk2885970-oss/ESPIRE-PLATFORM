from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Text, Table, Column, DateTime, Float, JSON
from datetime import datetime
from typing import List
from enum import Enum as PyEnum
from sqlalchemy import Enum

class Base(DeclarativeBase):
    pass

class Admin(Base):
    __tablename__ = "admin"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(25), nullable=False)
    email: Mapped[str] = mapped_column(String(101), unique=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hash_password: Mapped[str] = mapped_column(Text, nullable=False)

class Map_FreeFireMax(PyEnum):
    Bermuda = "Bermuda"
    Purgatory = "Purgatory"
    Kalahari = "Kalahari"
    Alpine = "Alpine"
    Nexterra = "Nexterra"
    Solara = "Solara"

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    team_name: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    hash_password: Mapped[str] = mapped_column(Text, nullable=False)
    performances: Mapped[List["MatchPerformance"]] = relationship("MatchPerformance", back_populates="team")

    def __repr__(self):
        return f"<team_id: {self.id}, team_name: {self.team_name}>"

class Match(Base):
    __tablename__ = "matches"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    match_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    performances: Mapped[List["MatchPerformance"]] = relationship("MatchPerformance", back_populates="match")

    def __repr__(self):
        return f"<match_id: {self.id}, date: {self.match_date}>"

class MatchPerformance(Base):
    __tablename__ = "matchPerformance"
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    map_name: Mapped[Map_FreeFireMax] = mapped_column(
        Enum(Map_FreeFireMax, name="freefire_map", native_enum=False),
        primary_key=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    kills: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[str] = mapped_column(String(50), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    match: Mapped["Match"] = relationship("Match", back_populates="performances")
    team: Mapped["Team"] = relationship("Team", back_populates="team")

    @property
    def team_name(self) -> str:
        return self.team.team_name if self.team else "Unknown"

class Map(Base):
    __tablename__ = "maps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Map_FreeFireMax] = mapped_column(
        Enum(Map_FreeFireMax, name="freefire_map", native_enum=False),
        unique=True, nullable=False
    )

class CommunityPost(Base):
    __tablename__ = "community_posts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"))
    table_data: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[int] = mapped_column(ForeignKey("admin.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"))
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admin.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    post: Mapped["CommunityPost"] = relationship("CommunityPost", back_populates="comments")


