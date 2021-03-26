from logging import getLogger

import ckan.lib.helpers as h
import ckan.plugins as p
import ckan.lib.datapreview as datapreview
import urlparse
from pylons import config

log = getLogger(__name__)

import ckan.lib.uploader as uploader

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from pylons import config

def get_proxified_resource_url(data_dict, proxy_schemes=['http','https']):
    '''
    :param data_dict: contains a resource and package dict
    :type data_dict: dictionary
    :param proxy_schemes: list of url schemes to proxy for.
    :type data_dict: list
    '''

    ckan_url = config.get('ckan.site_url', '//localhost:5000')
    url = data_dict['resource']['url']
    scheme = urlparse.urlparse(url).scheme
    compare_domains = datapreview.compare_domains
    if not compare_domains([ckan_url, url]) and scheme in proxy_schemes:
        url = h.url_for(
            action='proxy_resource',
            controller='ckanext.resourceproxy.controller:ProxyController',
            id=data_dict['package']['name'],
            resource_id=data_dict['resource']['id'])
        log.info('Proxified url is {0}'.format(url))

    if 's3filestore' in config.get('ckan.plugins', ''):

        BASE_PATH = config.get('ckan.storage_path')
        AWS_ACCESS_KEY_ID = config.get('ckanext.s3filestore.aws_access_key_id')
        AWS_SECRET_ACCESS_KEY = config.get('ckanext.s3filestore.aws_secret_access_key')
        AWS_BUCKET_NAME = config.get('ckanext.s3filestore.aws_bucket_name')
        AWS_STORAGE_PATH = config.get('ckanext.s3filestore.aws_storage_path')

        s3_connection = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        bucket = s3_connection.get_bucket(AWS_BUCKET_NAME)
        k = Key(bucket)

        id=data_dict['resource']['package_id']
        resource_id=data_dict['resource']['id']
#        url = data_dict['resource']['url']

#        k.key = 'resources/' + resource_id + '/' +str(url.split('/')[-1])

#        if AWS_STORAGE_PATH:
#           k.key = AWS_STORAGE_PATH + '/' + k.key

        #tpath = 'http://www.gspf.jp/s1/ckan/dataset/'+str(id)+'/resource/'+str(resource_id)+'/download/'+str(url.split('/')[-1])
#        tpath = BASE_PATH +'/resources/'+str(resource_id[0:3])+'/'+str(resource_id[3:6])+'/'+str(resource_id[6:])
#        k.get_contents_to_filename(tpath)
#        k.set_contents_from_filename(tpath)
#        k.make_public()

    #url = data_dict['resource']['url']
    #url = 'http://gspf-resource.s3.amazonaws.com/ckan/resources/'+str(resource_id)+'/'+str(url.split('/')[-1])
    #url = 'http://www.gspf.jp/s1/ckan/dataset/'
    #url = 'http://web.gspf.jp/s1/ckan/dataset/'+str(id)+'/resource/'+str(resource_id)+'/download/'+str(url.split('/')[-1])

    return url


class ResourceProxy(p.SingletonPlugin):
    """A proxy for CKAN resources to get around the same
    origin policy for previews

    This extension implements the IRoute interface
      - ``IRoutes`` allows to add a route to the proxy action


    Instructions on how to use the extension:

    1. Import the proxy plugin if it exists
        ``import ckanext.resourceproxy.plugin as proxy``

    2. In you extension, make sure that the proxy plugin is
        enabled by checking the ``ckan.resource_proxy_enabled`` config variable.
        ``config.get('ckan.resource_proxy_enabled', False)``
    """
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)


    def before_map(self, m):
        m.connect('/dataset/{id}/resource/{resource_id}/proxy',
                    controller='ckanext.resourceproxy.controller:ProxyController',
                    action='proxy_resource')
        return m

    def get_helpers(self):
        return {'view_resource_url': self.view_resource_url}

    def view_resource_url(self, resource_view, resource,
                          package, proxy_schemes=['http','https']):
        '''
        Returns the proxy url if its availiable
        '''
        data_dict = {'resource_view': resource_view,
                     'resource': resource,
                     'package': package}
        return get_proxified_resource_url(data_dict,
                                          proxy_schemes=proxy_schemes)
