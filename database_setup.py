from flask import Flask, render_template
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class Owner(Base):
    __tablename__ = 'owner'
    id_owner = Column(Integer, primary_key=True)
    email = Column(String(500), nullable=False)
    image = Column(String(500), nullable=False)


class GiftCategory(Base):
    __tablename__ = 'categories'
    id_category = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    id_owner = Column(Integer, ForeignKey('owner.id_owner'))
    owner = relationship(Owner, backref="categories")


class GiftItems(Base):
    __tablename__ = 'gift_item'
    name = Column(String(250), nullable=False)
    id_item = Column(Integer, primary_key=True)
    madeIn = Column(String(250), nullable=False)
    img_url = Column(String(500), nullable=False)
    additional_info = Column(String(500))
    price = Column(String(10))
    id_category = Column(Integer, ForeignKey('categories.id_category'))
    categories = relationship(GiftCategory, backref="gift_item")

    @property
    def serialize(self):
        return {
            'name': self.name,
            'info': self.additional_info,
            'price': self.price,
            'img_url': self.img_url,
            'madeIn': self.madeIn
        }


engine = create_engine('sqlite:///gifts.db')
Base.metadata.create_all(engine)
