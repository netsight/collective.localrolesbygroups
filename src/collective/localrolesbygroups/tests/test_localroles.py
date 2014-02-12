import unittest2 as unittest

from Products.CMFCore.utils import getToolByName

from collective.localrolesbygroups.testing import \
    COLLECTIVE_LOCALROLESBYGROUPS_INTEGRATION_TESTING


class TestExample(unittest.TestCase):

    layer = COLLECTIVE_LOCALROLESBYGROUPS_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.qi_tool = getToolByName(self.portal, 'portal_quickinstaller')

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
