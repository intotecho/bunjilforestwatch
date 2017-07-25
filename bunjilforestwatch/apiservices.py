from googleapiclient.discovery import build
import httplib2
import settings
import eeservice
from googleapiclient import errors
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload
import logging

import io
from io import StringIO
try:
    from io import BytesIO
except ImportError:
    BytesIO = StringIO

def create_table_service():
    if not eeservice.initEarthEngineService():
        logging.error('Sorry, Server Credentials Error')
    credentials = eeservice.EarthEngineService.credentials
    http = credentials.authorize(httplib2.Http())
    return build(serviceName='fusiontables', version='v2', http=http,  developerKey=settings.MY_LOCAL_SERVICE_ACCOUNT)

def create_drive_service():
    if not eeservice.initEarthEngineService():
        logging.error('Sorry, Server Credentials Error')
    credentials = eeservice.EarthEngineService.credentials
    http = credentials.authorize(httplib2.Http())
    #return build(serviceName='drive', version='v3', http=http, credentials=credentials) #raised ValueError('Arguments http and credentials are mutually exclusive.')
    return build(serviceName='drive', version='v3', http=http)

'''
get_file(id)
'''
def read_file(file_id):
    #media_body = MediaIoBaseUpload(fh, mimetype='application/octet-stream', chunksize=1024 * 1024, resumable=False)

    drive_service = create_drive_service()
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    data = ""
    while done is False:
        status, done = downloader.next_chunk()
        print "Download %d%%." % int(status.progress() * 100)
    return fh.getvalue()

def delete_file(file_id):
  """Permanently delete a file, skipping the trash.

  Args:
    service: Drive API service instance.
    file_id: ID of the file to delete.
  """
  drive_service = create_drive_service()
  try:
    drive_service.files().delete(fileId=file_id).execute()
    return None
  except errors.HttpError, error:
    return 'Error deleting file : %s' % error


def create_folder(folderName, parentID=None, drive_service=None ):
    # Create a folder on Drive, returns the newely created folders ID
    if not drive_service:
        drive_service = create_drive_service()
    body = {
        'name': folderName,
        'mimeType': "application/vnd.google-apps.folder"
    }
    if parentID:
        body['parents'] = [parentID]
    root_folder = drive_service.files().create(body=body, fields='id').execute()
    logging.info('created folder %s' %root_folder['id'])
    make_file_public(drive_service, root_folder['id'] )
    return root_folder['id']


def create_file(fileName, parentID=None, drive_service=None, raw_data=None):
    '''
    Create a file on Drive, returns the newely created folders ID
    '''
    if not drive_service:
        drive_service = create_drive_service()
    body = {
        'name': fileName,
        'mimeType': "text/plain",
    }
    if parentID:
        body['parents'] = [parentID]

    if raw_data:
        fh = BytesIO(raw_data)
        media = MediaIoBaseUpload(fh, mimetype='text/plain',
                                  chunksize=1024 * 1024, resumable=True)
    else:
        media_body=None

    file = drive_service.files().create(body=body, fields='id',  media_body=media).execute()

    logging.info('created folder %s' %file['id'])
    make_file_public(drive_service, file['id'] )
    return file['id']


'''
returns id of the latest file whose parent is folder_id, and matching mime_type - or None
'''
def get_latest_file(folder_id):
    page_token = None
    drive_service = create_drive_service()
    query = "'%s' in parents and mimeType='application/json'" %folder_id
    print query
    while True:
        response = drive_service.files().list(q=query,
                                              #orderBy='modifiedTime',
                                              pageSize=10,
                                              fields='nextPageToken, files(id, name)',
                                              pageToken=page_token).execute()
        for file in response.get('files', []):
            # Process change
            logging.debug('Found file: %s (%s)' %(file.get('name'), file.get('id')))
            return file.get('id')
        return None
        #page_token = response.get('nextPageToken', None)
        #if page_token is None:
        #    break;




'''
@returns a list of file items that can be rendered.
'''
def get_folder_list(page_token=None):
    service = create_drive_service()
    param = {
        'pageSize' : 20,
        'fields'   : "nextPageToken, files(id, name,  mimeType, modifiedTime, size, iconLink, webContentLink, webViewLink)"
    }
    if page_token:
        param['pageToken'] = page_token
    results = service.files().list(**param).execute()
    page_token = results.get('nextPageToken')
    items = results.get('files', [])
    return page_token, items

'''
returns a rendered html string of folders
'''
def list_folders():
    service = create_drive_service()
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    listing = ""
    #listing = list_tasks() #TODO move to new url

    listing += '<h2><a href= "https://www.google.com/fusiontables/showtables">User\'s Fusion Tables</a></h2>'
    listing += '<h2><a href= "/admin/exports">List Earth Engine Export Tasks</a></h2>'

    if not items:
        listing += '<h2> No files found.</h2>'
    else:
        listing += '<h2> Files </h2>'
        for item in items:
            #make_file_public(service, item['id'])
            listing += '<ul>' +  '<a href="https://drive.google.com/open?id=' + item['id'] + '">' + item['name'] + '</a>' + " " +\
                     '<a href = "/admin/assets/delete/' + item['id'] + '" target="_blank"> [DELETE]<a>'
            listing += '<em>' + list_file_metadata(service, item['id']) + '</em></ul>'
    return listing
    #       'mimeType': "application/vnd.google-apps.folder"

def list_files_infolder(folder_id = None):
    service = create_drive_service()
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name, mimeType, selfLink, createdTime, size)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            make_file_public(service, item['id'])
            print('{0} ({1})'.format(item['name'], item['id']))

            #GET https://www.googleapis.com/drive/v2/files?q='BB0CHANGEDIDF5waGdzbUQ5aWs'+in+parents&key={YOUR_API_KEY}


def list_file_by_owner():
    drive_service = create_drive_service()
    #permissions = drive_service.permissions()
    # for pagination, see https://developers.google.com/drive/v3/web/search-parameters#examples
    query = "'%s' in owners and trashed = false" %settings.MY_LOCAL_SERVICE_ACCOUNT
    '''
    response = drive_service.files().list(q=query,
                                          spaces='drive',
                                          fields='nextPageToken, files(id, name)',
                                          pageToken=page_token).execute()
    '''
    response = drive_service.files().list(q=query).execute()

    output = "<h1>Files owned by application </h1><h2>%s</h2>" %settings.MY_LOCAL_SERVICE_ACCOUNT

    for file in response.get('files', []):
        # Process change
        #print 'Found file: %s (%s)' % (file.get('name'), file.get('id'))
        output += '<ul>' + fusiontable_url(file.get('id'), file.get('name')) + \
                  '<a href = "/admin/assets/delete/' + file.get('id') + '" target="_blank"> DELETE<a></ul>'
    return output


def list_file_metadata(service, file_id):
    """
    Return a file's metadata as a string.
    Args:
      service: Drive API service instance.
      file_id: ID of the file to print metadata for.
    """
    msg = ""
    try:
        file = service.files().get(fileId=file_id).execute()
        msg += '<br/>: %s' % file['mimeType']
    except errors.HttpError, error:
        msg += 'list_file_metadata() error : %s' % error
    return msg


def list_tables():
    service = create_table_service()
    return service.table().list().execute()
    #GET https://www.googleapis.com/drive/v2/files?q='BB0CHANGEDIDF5waGdzbUQ5aWs'+in+parents&key={YOUR_API_KEY}


def fusiontable_url(id, name):
    '''
    @params id: The docid of the table
    @params name: The link text to display.
    @returns:  a HTML formatted string that is a link to a fusion table
    '''
    return '<a href="https://www.google.com/fusiontables/data?docid=' + id + '">' + name + '</a> '

def make_file_public(drive_service, fileId):
    permissions = drive_service.permissions()
    permissions.create(fileId=fileId,
                       body={"type": "anyone", "role": "writer"},
                       sendNotificationEmail=False).execute()

def make_files_public(items):
    service = create_drive_service()
    permissions = drive_service.permissions()
    permissions.create(fileId=fileId,
                       body={"type": "anyone", "role": "reader"},
                       sendNotificationEmail=False).execute()

'''
NOT USED
'''
def _makePublic_callback(request_id, response, exception):
    if exception:
        # Handle error
        print exception
    else:
        print "Permission Id: %s" % response.get('id')

#FUNCTION NOT USED
def makePublic(drive_service, file_id, name):
    new_permission = {
        #'value': 'bunjilforestwatch.net',
        'type': 'anyone',
        'role': 'reader',
        "allowFileDiscovery": False,
        #"displayName": name
    }
    try:
        return drive_service.permissions().create(
            fileId=file_id, body=new_permission).execute()
    except Exception, e:
        print 'makePublic() An error occurred: %s' % e
    return None

    batch = drive_service.new_batch_http_request(callback=_makePublic_callback)
    user_permission = {
        'type': 'anyone',
        'role': 'reader',
        "allowFileDiscovery": False,
        "displayName": name
    }
    batch.add(drive_service.permissions().create(
        fileId=file_id,
        body=user_permission,
        fields='id',
    ))
    domain_permission = {
        'type': 'domain',
        'role': 'reader',
        'domain': 'bunjilforestwatch.net'
    }
    batch.add(drive_service.permissions().create(
        fileId=file_id,
        body=domain_permission,
        fields='id',
    ))
    batch.execute()
    return batch

