from Products.CMFCore.utils import getToolByName

from collective.localrolesbygroups.testing import \
    COLLECTIVE_LOCALROLESBYGROUPS_INTEGRATION_TESTING
from collective.localrolesbygroups.browser.sharing import GROUP_KEY

from plone.app.workflow.tests.base import WorkflowTestCase
from plone import api

#class TestExample(unittest.TestCase):
class TestLocalRoles(WorkflowTestCase):

    layer = COLLECTIVE_LOCALROLESBYGROUPS_INTEGRATION_TESTING

    def afterSetUp(self):
        WorkflowTestCase.afterSetUp(self)
        self.qi_tool = getToolByName(self.portal, 'portal_quickinstaller')

        self.setRoles(('Manager', ))
        self.portal.acl_users._doAddUser('member1', 'secret', ['Member'], [])
        self.portal.acl_users._doAddUser('member2', 'secret', ['Member'], [])
        self.portal.acl_users._doAddUser('member3', 'secret', ['Member'], [])


        self.folder.invokeFactory('Document', id='doc')
        self.doc = self.folder.doc


    def test_product_is_installed(self):
        """ Validate that our products GS profile has been run and the product
            installed
        """
        pid = 'collective.localrolesbygroups'
        installed = [p['id'] for p in self.qi_tool.listInstalledProducts()]
        self.assertTrue(pid in installed,
                        'package appears not to have been installed')

    def test_lr_groups_plugin_created(self):
        plugins = self.portal.acl_users.objectIds()
        self.assertTrue('lr_groups' in plugins, 'Local roles group plugin not created')

    def test_lr_groups_add_local_role(self):
        plugins = self.portal.acl_users.objectIds()
        self.assertTrue('lr_groups' in plugins, 'Local roles group plugin not created')

        role = 'Contributor'
        group_id = "%s-%s-%s" % (GROUP_KEY, api.content.get_uuid(self.folder), role)
        
        api.user.grant_roles(username='member1',
                             roles=[role],
                             obj=self.folder,
                             )

        self.assertTrue(group_id in self.portal.acl_users.lr_groups.getGroupIds(), 'Local role group not created')

