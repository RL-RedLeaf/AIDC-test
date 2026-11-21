from .validators import _k_factor, _nonnegative


def total_capacity(grid_mw, self_generation_mw, k_factor, pcc_mw=None):
    """正文式 (2)、(7)。专用接线可省略共享关口上限。"""
    _nonnegative("P_grid", grid_mw)
    _nonnegative("P_self", self_generation_mw)
    _k_factor(k_factor)
    facility_mw = grid_mw + self_generation_mw
    if pcc_mw is not None:
        _nonnegative("C_PCC_mw", pcc_mw)
        facility_mw = min(facility_mw, pcc_mw)
    return facility_mw / k_factor, facility_mw
