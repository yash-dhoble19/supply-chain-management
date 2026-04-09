"""
Manufacturing service - handles manufacturing goods operations.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas.manufacturing


def get_all_manufacturing_goods(db: Session) -> List[models.ManufacturingGoods]:
    return db.query(models.ManufacturingGoods).all()


def get_manufacturing_goods_by_id(db: Session, goods_id: int) -> Optional[models.ManufacturingGoods]:
    return db.query(models.ManufacturingGoods).filter(models.ManufacturingGoods.id == goods_id).first()


def get_manufacturing_goods_by_sku(db: Session, sku: str) -> Optional[models.ManufacturingGoods]:
    return db.query(models.ManufacturingGoods).filter(models.ManufacturingGoods.sku == sku).first()


def create_manufacturing_goods(db: Session, goods: schemas.manufacturing.ManufacturingGoodsCreate) -> models.ManufacturingGoods:
    db_goods = models.ManufacturingGoods(
        sku=goods.sku,
        product_name=goods.product_name,
        status=goods.status,
        progress=goods.progress,
        start_date=goods.start_date,
        est_completion=goods.est_completion,
        unit_price=goods.unit_price,
    )
    db.add(db_goods)
    db.commit()
    db.refresh(db_goods)
    return db_goods


def update_manufacturing_goods(db: Session, goods_id: int, update_data: schemas.manufacturing.ManufacturingGoodsUpdate) -> Optional[models.ManufacturingGoods]:
    db_goods = get_manufacturing_goods_by_id(db, goods_id)
    if not db_goods:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_goods, key, value)

    db.commit()
    db.refresh(db_goods)
    return db_goods


def get_completed_manufacturing_goods(db: Session) -> List[models.ManufacturingGoods]:
    return db.query(models.ManufacturingGoods).filter(models.ManufacturingGoods.status == "Done").all()
# anything
