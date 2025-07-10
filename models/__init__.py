from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models that actually exist and make them available at package level
from .item_master import ItemMaster
from .machinery import Machinery
from .department import Department
from .production import Production
from .packing import Packing
from .raw_material_stocktake import RawMaterialStocktake
from .inventory import Inventory
from .allergen import Allergen
from .item_type import ItemType
from .soh import SOH
from .filling import Filling
from .category import Category
from .uom import UOM
from .user import User
from .recipe_master import RecipeMaster
from .usage_report_table import UsageReportTable
from .raw_material_report_table import RawMaterialReportTable

# FinishedGoods is commented out in the file, so skip importing it
try:
    from .finished_goods import FinishedGoods
except ImportError:
    FinishedGoods = None

# For models that might be referenced but don't exist, create aliases or placeholders
try:
    from .recipe import Recipe
except ImportError:
    # If recipe doesn't exist, alias RecipeMaster as Recipe
    Recipe = RecipeMaster

try:
    from .recipe_detail import RecipeDetail
except ImportError:
    RecipeDetail = None

try:
    from .production_detail import ProductionDetail
except ImportError:
    ProductionDetail = None

try:
    from .packing_detail import PackingDetail
except ImportError:
    PackingDetail = None

try:
    from .raw_material_report import RawMaterialReport
except ImportError:
    RawMaterialReport = None

try:
    from .item_allergen import ItemAllergen
except ImportError:
    ItemAllergen = None

try:
    from .item_hierarchy import ItemHierarchy
except ImportError:
    ItemHierarchy = None

try:
    from .bom import BOM
except ImportError:
    BOM = None

try:
    from .bom_detail import BOMDetail
except ImportError:
    BOMDetail = None

try:
    from .calculation_factor import CalculationFactor
except ImportError:
    CalculationFactor = None

try:
    from .soh_detail import SOHDetail
except ImportError:
    SOHDetail = None

try:
    from .joining import Joining
except ImportError:
    Joining = None

try:
    from .joining_detail import JoiningDetail
except ImportError:
    JoiningDetail = None

try:
    from .wip import WIP
except ImportError:
    WIP = None

try:
    from .wip_detail import WIPDetail
except ImportError:
    WIPDetail = None

try:
    from .production_filling import ProductionFilling
except ImportError:
    ProductionFilling = None

try:
    from .production_filling_detail import ProductionFillingDetail
except ImportError:
    ProductionFillingDetail = None

try:
    from .production_packing import ProductionPacking
except ImportError:
    ProductionPacking = None

try:
    from .production_packing_detail import ProductionPackingDetail
except ImportError:
    ProductionPackingDetail = None

try:
    from .production_total import ProductionTotal
except ImportError:
    ProductionTotal = None

try:
    from .production_total_detail import ProductionTotalDetail
except ImportError:
    ProductionTotalDetail = None

try:
    from .usage_report import UsageReport
except ImportError:
    UsageReport = None

try:
    from .usage_report_detail import UsageReportDetail
except ImportError:
    UsageReportDetail = None

# Legacy init_models function for backward compatibility
def init_models():
    # Models are already imported above, so this function is now a no-op
    pass