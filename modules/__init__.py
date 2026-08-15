from modules.product_intel import MODULE as PRODUCT_INTEL
from modules.review_intel import MODULE as REVIEW_INTEL

MODULES = [PRODUCT_INTEL, REVIEW_INTEL]
BY_KEY = {m.key: m for m in MODULES}
