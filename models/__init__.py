from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models after db is defined
def init_models():
    from .item_master import ItemMaster
    from .machinery import Machinery
    from .department import Department
    from .recipe import Recipe
    from .recipe_detail import RecipeDetail
    from .production import Production
    from .production_detail import ProductionDetail
    from .packing import Packing
    from .packing_detail import PackingDetail
    from .raw_material_report import RawMaterialReport
    from .raw_material_stocktake import RawMaterialStocktake
    from .inventory import Inventory
    from .allergen import Allergen
    from .item_allergen import ItemAllergen
    from .item_type import ItemType
    from .item_hierarchy import ItemHierarchy
    from .bom import BOM
    from .bom_detail import BOMDetail
    from .calculation_factor import CalculationFactor
    from .soh import SOH
    from .soh_detail import SOHDetail
    from .joining import Joining
    from .joining_detail import JoiningDetail
    from .wip import WIP
    from .wip_detail import WIPDetail
    from .production_filling import ProductionFilling
    from .production_filling_detail import ProductionFillingDetail
    from .production_packing import ProductionPacking
    from .production_packing_detail import ProductionPackingDetail
    from .production_total import ProductionTotal
    from .production_total_detail import ProductionTotalDetail
    from .usage_report import UsageReport
    from .usage_report_detail import UsageReportDetail
    from .raw_material_report_table import RawMaterialReportTable
    from .usage_report_table import UsageReportTable