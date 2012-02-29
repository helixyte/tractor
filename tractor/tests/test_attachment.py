"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

from StringIO import StringIO
from datetime import datetime
from tractor.attachment import AttachmentWrapper
from tractor.attachment import Base64Converter
from tractor.tests.base import BaseTestCase
from xmlrpclib import Binary
import zipfile


class Base64ConverterTestCase(BaseTestCase):

    def test_encode_string(self):
        test_str = 'This is a string for base64 conversion testing.'
        exp_conv = Binary(test_str)
        self.assert_equal(Base64Converter.encode_string(test_str), exp_conv)

    def test_encode_stream(self):
        test_stream = StringIO('This is a stream for base64 conversion testing.')
        exp_conv = Binary(test_stream.read())
        self.assert_equal(Base64Converter.encode_stream(test_stream), exp_conv)
        test_stream.close()

    def test_encode_zip_stream(self):
        zip_stream = StringIO()
        archive = zipfile.ZipFile(zip_stream, 'a', zipfile.ZIP_DEFLATED, False)
        archive.writestr('file1', 'test stream 1')
        archive.writestr('file2', 'test stream 2')
        for zfile in archive.filelist: zfile.create_system = 0
        archive.close()
        zip_stream.seek(0)
        exp_conv = Binary(zip_stream.getvalue())
        self.assert_equal(Base64Converter.encode_zip_stream(zip_stream),
                          exp_conv)
        zip_stream.close()

    def test_decode_string(self):
        test_str = 'This is a string for base64 conversion testing.'
        conv = Base64Converter.encode_string(test_str)
        self.assert_equal(Base64Converter.decode_to_string(conv), test_str)

    def test_decode_stream(self):
        test_stream = StringIO('This is a stream for base64 conversion testing.')
        conv = Base64Converter.encode_stream(test_stream)
        decoded_conv = Base64Converter.decode_to_stream(conv)
        decoded_cont = decoded_conv.read()
        test_stream.seek(0)
        exp_cont = test_stream.read()
        self.assert_equal(decoded_cont, exp_cont)

    def test_decode_zip_file_data(self):
        zip_stream = StringIO()
        archive = zipfile.ZipFile(zip_stream, 'a', zipfile.ZIP_DEFLATED, False)
        archive.writestr('file1', 'test stream 1')
        archive.writestr('file2', 'test stream 2')
        for zfile in archive.filelist: zfile.create_system = 0
        archive.close()
        zip_stream.seek(0)
        conv = Base64Converter.encode_zip_stream(zip_stream)
        decoded_conv = Base64Converter.decode_to_stream(conv)
        ret_archive = zipfile.ZipFile(decoded_conv, 'a', zipfile.ZIP_DEFLATED,
                                      False)
        content1 = None
        content2 = None
        self.assert_equal(len(ret_archive.namelist()), 2)
        for file_name in ret_archive.namelist():
            if file_name == 'file1':
                content1 = ret_archive.read(file_name)
                self.assert_equal(content1, 'test stream 1')
                self.assert_not_equal(content2, 'test stream 2')
            else:
                content2 = ret_archive.read(file_name)
                self.assert_equal(content2, 'test stream 2')
                self.assert_not_equal(content2, 'test stream 1')

class AttachmentTestCase(BaseTestCase):

    def set_up(self):
        BaseTestCase.set_up(self)
        self.init_data = dict(content='Important attachment content.',
                              file_name='test_file1.txt',
                              description='A test file.',
                              size=14,
                              author='user1',
                              time=None)

    def test_init(self):
        att = AttachmentWrapper(**self.init_data)
        for attr_name, exp_value in self.init_data.iteritems():
            self.assert_equal(getattr(att, attr_name), exp_value)

    def test_create_from_trac_data(self):
        file_name = 'test_file1.txt'
        description = 'A test file.'
        size = len(file_name)
        time = datetime
        author = 'user1'
        trac_data = (file_name, description, size, time, author)
        att = AttachmentWrapper.create_from_trac_data(trac_data)
        self.init_data['content'] = None
        self.init_data['time'] = time
        for attr_name, exp_value in self.init_data.iteritems():
            self.assert_equal(getattr(att, attr_name), exp_value)

    def test_get_base64_data_for_upload(self):
        # Test string
        test_str = 'This is a string for base64 conversion testing.'
        self.init_data['content'] = test_str
        exp_conv = Base64Converter.encode_string(test_str)
        att = AttachmentWrapper(**self.init_data)
        self.assert_equal(att.get_base64_data_for_upload(), exp_conv)
        # Test stream
        test_stream = StringIO('This is a stream for base64 conversion testing.')
        exp_conv = Base64Converter.encode_stream(test_stream)
        self.init_data['content'] = test_stream
        att = AttachmentWrapper(**self.init_data)
        self.assert_equal(att.get_base64_data_for_upload(), exp_conv)
        # Test file map
        file_map = dict(file1='test stream 1', file2='test stream 2')
        zip_stream = StringIO()
        archive = zipfile.ZipFile(zip_stream, 'a', zipfile.ZIP_DEFLATED, False)
        for fn, content in file_map.iteritems(): archive.writestr(fn, content)
        for zfile in archive.filelist: zfile.create_system = 0
        archive.close()
        zip_stream.seek(0)
        exp_conv = Base64Converter.encode_zip_stream(zip_stream)
        self.init_data['content'] = file_map
        att = AttachmentWrapper(**self.init_data)
        self.assert_equal(att.get_base64_data_for_upload(), exp_conv)
        # Test error raising
        self.init_data['content'] = 1
        att = AttachmentWrapper(**self.init_data)
        self.assert_raises(TypeError, att.get_base64_data_for_upload)
