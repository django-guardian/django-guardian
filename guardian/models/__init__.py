from .models import (
    UserObjectPermissionBase,
    UserObjectPermissionAbstract,
    GroupObjectPermissionBase,
    GroupObjectPermissionAbstract,
    Permission,
    Group
)

# Must import after .models
# When .models is loaded, default generic object permissions are created
# The following statements may redirect external references to custom
# generic object permission models
from guardian.utils import get_user_obj_perms_model, get_group_obj_perms_model
UserObjectPermission = get_user_obj_perms_model()
GroupObjectPermission = get_group_obj_perms_model()

