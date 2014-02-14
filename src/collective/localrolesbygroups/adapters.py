from zope.interface import Interface, implements
from zope.component import adapts
from borg.localrole.interfaces import ILocalRoleProvider
from utils import expand_roles

class LocalRolesByGroupsLocalRoleAdapter(object):
    implements(ILocalRoleProvider)
    adapts(Interface)

    def __init__(self, context):
        self.context = context

    @property
    def _rolemap(self):
        rolemap = getattr(self.context, '__ac_local_roles__', {})
        # None is the default value from AccessControl.Role.RoleMananger                                                                                                              
        if rolemap is None:
            return {}
        if callable(rolemap):
            rolemap = rolemap()
        return rolemap

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context"""
        return self._rolemap.get(principal_id, [])

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:                                                                                                                      
        (principal_id, [role1, role2])"""
        return expand_roles(self.context, self._rolemap.items())
