from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces

def configureLocalRolesByGroups(context):

    marker = 'collective.localrolesbygroups.profiles.marker'
    if context.readDataFile(marker) is None:
        return

    site = context.getSite()
    pas = getToolByName(site, 'acl_users')

    if "lr_groups" not in pas.objectIds():
        factory = pas.manage_addProduct['PlonePAS']
        factory.manage_addGroupManager(
            'lr_groups',
            "Local Roles as Groups plugin"
        )

    # Activate all but Enumeration, as we don't want to show these groups in UI:
    activatePluginInterfaces(site, "lr_groups",
                             disable=['IGroupEnumerationPlugin'])
