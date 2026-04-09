from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import database
from models import PublishedGoods, Product
from schemas.published_goods import PublishedGoodsCreate, PublishedGoodsOut

router = APIRouter(prefix="/api/published-goods", tags=["Published Goods"])

@router.get("/", response_model=list[PublishedGoodsOut])
def get_published_goods(db: Session = Depends(database.get_db)):
    goods = db.query(PublishedGoods).order_by(PublishedGoods.published_at.desc()).all()
    return goods

@router.post("/", response_model=PublishedGoodsOut)
def create_published_goods(payload: PublishedGoodsCreate, db: Session = Depends(database.get_db)):
    # Optionally validate product exists
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    published = PublishedGoods(**payload.dict())
    db.add(published)
    db.commit()
    db.refresh(published)
    return published

@router.delete("/{goods_id}")
def delete_published_goods(goods_id: int, db: Session = Depends(database.get_db)):
    goods = db.query(PublishedGoods).filter(PublishedGoods.id == goods_id).first()
    if not goods:
        raise HTTPException(status_code=404, detail="Published goods not found")
    db.delete(goods)
    db.commit()
    return {"message": "Deleted"}

# anything
