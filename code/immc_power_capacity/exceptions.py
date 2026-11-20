class CapacityModelError(ValueError):
    """输入数据不足或无法求解时的基础异常."""


class ValidationError(CapacityModelError):
    """模型输入不满足单位、范围或完整性要求."""


class InfeasibleError(CapacityModelError):
    """附录 A 光储问题无可行运行安排."""
