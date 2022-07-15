# rocks_if.py
# 20 may 2022
#
# copied from:
# https://github.com/DrInfy/sharpy-sc2/blob/5707ab55460ccfc7e872f73fb42bf5d5118668c7/sharpy/general/rocks.py
#

from sc2.ids.unit_typeid import UnitTypeId


class Rocks_if:
    unbuildable_rocks = {
        UnitTypeId.UNBUILDABLEROCKSDESTRUCTIBLE,
        UnitTypeId.UNBUILDABLEBRICKSDESTRUCTIBLE,
        UnitTypeId.UNBUILDABLEPLATESDESTRUCTIBLE,
        UnitTypeId.UNBUILDABLEBRICKSSMALLUNIT,
        UnitTypeId.UNBUILDABLEPLATESSMALLUNIT,
        UnitTypeId.UNBUILDABLEPLATESUNIT,
        UnitTypeId.UNBUILDABLEROCKSSMALLUNIT,
        UnitTypeId.UNBUILDABLEBRICKSUNIT,
        UnitTypeId.UNBUILDABLEROCKSUNIT,
    }

    breakable_rocks_2x2 = {
        UnitTypeId.ROCKS2X2NONCONJOINED,
    }

    breakable_rocks_4x4 = {
        UnitTypeId.DESTRUCTIBLECITYDEBRIS4X4,
        UnitTypeId.DESTRUCTIBLEDEBRIS4X4,
        UnitTypeId.DESTRUCTIBLEICE4X4,
        UnitTypeId.DESTRUCTIBLEROCK4X4,
        UnitTypeId.DESTRUCTIBLEROCKEX14X4,
    }

    breakable_rocks_4x2 = {
        UnitTypeId.DESTRUCTIBLECITYDEBRIS2X4HORIZONTAL,
        UnitTypeId.DESTRUCTIBLEICE2X4HORIZONTAL,
        UnitTypeId.DESTRUCTIBLEROCK2X4HORIZONTAL,
        UnitTypeId.DESTRUCTIBLEROCKEX12X4HORIZONTAL,
    }

    breakable_rocks_2x4 = {
        UnitTypeId.DESTRUCTIBLECITYDEBRIS2X4VERTICAL,
        UnitTypeId.DESTRUCTIBLEICE2X4VERTICAL,
        UnitTypeId.DESTRUCTIBLEROCK2X4VERTICAL,
        UnitTypeId.DESTRUCTIBLEROCKEX12X4VERTICAL,
    }

    breakable_rocks_6x2 = {
        UnitTypeId.DESTRUCTIBLECITYDEBRIS2X6HORIZONTAL,
        UnitTypeId.DESTRUCTIBLEICE2X6HORIZONTAL,
        UnitTypeId.DESTRUCTIBLEROCK2X6HORIZONTAL,
        UnitTypeId.DESTRUCTIBLEROCKEX12X6HORIZONTAL,
    }

    breakable_rocks_2x6 = {
        UnitTypeId.DESTRUCTIBLECITYDEBRIS2X6VERTICAL,
        UnitTypeId.DESTRUCTIBLEICE2X6VERTICAL,
        UnitTypeId.DESTRUCTIBLEROCK2X6VERTICAL,
        UnitTypeId.DESTRUCTIBLEROCKEX12X6VERTICAL,
    }

    breakable_rocks_6x6 = {
        UnitTypeId.DESTRUCTIBLECITYDEBRIS6X6,
        UnitTypeId.DESTRUCTIBLEDEBRIS6X6,
        UnitTypeId.DESTRUCTIBLEICE6X6,
        UnitTypeId.DESTRUCTIBLEROCK6X6,
        UnitTypeId.DESTRUCTIBLEROCKEX16X6,
    }

    breakable_rocks_diag_BLUR = {
        UnitTypeId.DESTRUCTIBLECITYDEBRISHUGEDIAGONALBLUR,
        UnitTypeId.DESTRUCTIBLEDEBRISRAMPDIAGONALHUGEBLUR,
        UnitTypeId.DESTRUCTIBLEICEDIAGONALHUGEBLUR,
        UnitTypeId.DESTRUCTIBLEROCKEX1DIAGONALHUGEBLUR,
        UnitTypeId.DESTRUCTIBLERAMPDIAGONALHUGEBLUR,
    }

    breakable_rocks_diag_ULBR = {
        UnitTypeId.DESTRUCTIBLECITYDEBRISHUGEDIAGONALULBR,
        UnitTypeId.DESTRUCTIBLEDEBRISRAMPDIAGONALHUGEULBR,
        UnitTypeId.DESTRUCTIBLEICEDIAGONALHUGEULBR,
        UnitTypeId.DESTRUCTIBLEROCKEX1DIAGONALHUGEULBR,
        UnitTypeId.DESTRUCTIBLERAMPDIAGONALHUGEULBR,
    }
