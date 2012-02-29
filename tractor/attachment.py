"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

from StringIO import StringIO
from xmlrpclib import Binary
import zipfile

__docformat__ = 'reStructuredText en'
__all__ = ['AttachmentWrapper',
           'Base64Converter']


class AttachmentWrapper(object):
    """
    Convenience class for attachment data.

    :Note: A attachment wrapper always treats one file. You can pass several
        files though, which will then be converted into a zip archive before
        upload. Pass the files as dictionary using the file names as keys
        and the content of the files as values.
    """

    def __init__(self, content, file_name, description,
                 size=None,
                 author=None,
                 time=None):

        #: The content can either be a string, a stream or dictionary
        #: with file names as keys and streams or contents as values.
        #: If you use a dictionary, the attachment wil be converted
        #: into a zip archive.
        self.content = content

        #: The name of the file or zip archive in the trac.
        self.file_name = file_name

        #: A short description of the file.
        self.description = description

        #: The author will not be uploaded and thus, does not need to be set
        #: for upload.
        self.author = author
        #: The size will not be determined by the trac itself and thus, does
        #: not need to be set for upload.
        self.size = size
        #: The time will not be determined by the trac itself and thus, does
        #: not need to be set for upload.
        self.time = time

    @classmethod
    def create_from_trac_data(cls, trac_attachment_data):
        """
        Converts the trac ticket return value into a :class:`AttachmentWrapper`
        object.
        """
        attachment = AttachmentWrapper(file_name=trac_attachment_data[0],
                                description=trac_attachment_data[1],
                                size=trac_attachment_data[2],
                                time=trac_attachment_data[3],
                                author=trac_attachment_data[4],
                                content=None)
        return attachment

    def get_base64_data_for_upload(self):
        """
        Returns a base64-encoded string for the file upload.

        :raise TypeError: If the content is an unsupported data type.
        """
        if isinstance(self.content, StringIO):
            return Base64Converter.encode_stream(self.content)

        elif isinstance(self.content, basestring):
            return Base64Converter.encode_string(self.content)

        elif isinstance(self.content, dict):

            zip_stream = StringIO()
            archive = zipfile.ZipFile(zip_stream, 'a', zipfile.ZIP_DEFLATED,
                                      False)

            for file_name, f_content in self.content.iteritems():
                if isinstance(f_content, StringIO):
                    archive.writestr(file_name, f_content.read())
                else:
                    archive.writestr(file_name, f_content)
            # A permission issue.
            for zfile in archive.filelist: zfile.create_system = 0
            archive.close()

            return Base64Converter.encode_zip_stream(zip_stream)

        else:
            raise TypeError('Unsupported data type "%s".' \
                            % (self.content.__class__.__name__))

    def __str__(self):
        return self.file_name

    def __repr__(self):
        str_format = '<%s, file name: %s, description: %s>'
        params = (self.__class__.__name__, self.file_name, self.description)
        return str_format % params


class Base64Converter(object):
    """
    base64 encoding and deconding methods.
    """

    @classmethod
    def encode_string(cls, text):
        """
        Returns the encoded string.
        """
        return Binary(text)

    @classmethod
    def encode_stream(cls, stream):
        """
        Returns the encoded content of the stream.
        """
        stream.seek(0)
        content = stream.read()
        return cls.encode_string(content)

    @classmethod
    def encode_zip_stream(cls, zip_stream):
        """
        Returns the encoded content of a zip stream.
        """
        zip_stream.seek(0)
        return Binary(zip_stream.getvalue())

    @classmethod
    def decode_to_string(cls, base64_data):
        """
        Returns a decoded string.
        """
        return base64_data.data

    @classmethod
    def decode_to_stream(cls, base64_data):
        """
        Returns the decoded content of the base64 encoded binary as stream.
        """
        stream = StringIO(base64_data.data)
        stream.seek(0)
        return stream

