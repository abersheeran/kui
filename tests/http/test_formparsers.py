import os
import random
import sys
import tempfile
import unittest
from io import BytesIO
from unittest.mock import Mock

import yaml
from starlette.datastructures import UploadFile
from starlette.testclient import TestClient

from indexpy.http.formparsers import (
    Base64Decoder,
    BaseParser,
    DecodeError,
    Field,
    File,
    FileError,
    FormParserError,
    MultipartParseError,
    MultipartParser,
    QuerystringParseError,
    QuerystringParser,
    QuotedPrintableDecoder,
    _user_safe_decode,
    parse_options_header,
)
from indexpy.http.request import Request
from indexpy.http.responses import JSONResponse

# Get the current directory for our later test cases.
curr_dir = os.path.abspath(os.path.dirname(__file__))


def force_bytes(val):
    if isinstance(val, str):
        val = val.encode(sys.getfilesystemencoding())

    return val


class TestField(unittest.TestCase):
    def setUp(self):
        self.f = Field("foo")

    def test_name(self):
        self.assertEqual(self.f.field_name, "foo")

    def test_data(self):
        self.f.write(b"test123")
        self.assertEqual(self.f.value, b"test123")

    def test_cache_expiration(self):
        self.f.write(b"test")
        self.assertEqual(self.f.value, b"test")
        self.f.write(b"123")
        self.assertEqual(self.f.value, b"test123")

    def test_finalize(self):
        self.f.write(b"test123")
        self.f.finalize()
        self.assertEqual(self.f.value, b"test123")

    def test_close(self):
        self.f.write(b"test123")
        self.f.close()
        self.assertEqual(self.f.value, b"test123")

    def test_from_value(self):
        f = Field.from_value(b"name", b"value")
        self.assertEqual(f.field_name, b"name")
        self.assertEqual(f.value, b"value")

        f2 = Field.from_value(b"name", None)
        self.assertEqual(f2.value, None)

    def test_equality(self):
        f1 = Field.from_value(b"name", b"value")
        f2 = Field.from_value(b"name", b"value")

        self.assertEqual(f1, f2)

    def test_equality_with_other(self):
        f = Field.from_value(b"foo", b"bar")
        self.assertFalse(f == b"foo")
        self.assertFalse(b"foo" == f)

    def test_set_none(self):
        f = Field(b"foo")
        self.assertEqual(f.value, b"")

        f.set_none()
        self.assertEqual(f.value, None)


class TestFile(unittest.TestCase):
    def setUp(self):
        self.c = {}
        self.d = force_bytes(tempfile.mkdtemp())
        self.f = File(b"foo.txt", config=self.c)

    def assert_data(self, data):
        f = self.f.file_object
        f.seek(0)
        self.assertEqual(f.read(), data)
        f.seek(0)
        f.truncate()

    def assert_exists(self):
        full_path = os.path.join(self.d, self.f.actual_file_name)
        self.assertTrue(os.path.exists(full_path))

    def test_simple(self):
        self.f.write(b"foobar")
        self.assert_data(b"foobar")

    def test_invalid_write(self):
        m = Mock()
        m.write.return_value = 5
        self.f._fileobj = m
        v = self.f.write(b"foobar")
        self.assertEqual(v, 5)

    def test_file_fallback(self):
        self.c["MAX_MEMORY_FILE_SIZE"] = 1

        self.f.write(b"1")
        self.assertTrue(self.f.in_memory)
        self.assert_data(b"1")

        self.f.write(b"123")
        self.assertFalse(self.f.in_memory)
        self.assert_data(b"123")

        # Test flushing too.
        old_obj = self.f.file_object
        self.f.flush_to_disk()
        self.assertFalse(self.f.in_memory)
        self.assertIs(self.f.file_object, old_obj)

    def test_file_fallback_with_data(self):
        self.c["MAX_MEMORY_FILE_SIZE"] = 10

        self.f.write(b"1" * 10)
        self.assertTrue(self.f.in_memory)

        self.f.write(b"2" * 10)
        self.assertFalse(self.f.in_memory)

        self.assert_data(b"11111111112222222222")

    def test_file_name(self):
        # Write to this dir.
        self.c["UPLOAD_DIR"] = self.d
        self.c["MAX_MEMORY_FILE_SIZE"] = 10

        # Write.
        self.f.write(b"12345678901")
        self.assertFalse(self.f.in_memory)

        # Assert that the file exists
        self.assertIsNotNone(self.f.actual_file_name)
        self.assert_exists()

    def test_file_full_name(self):
        # Write to this dir.
        self.c["UPLOAD_DIR"] = self.d
        self.c["UPLOAD_KEEP_FILENAME"] = True
        self.c["MAX_MEMORY_FILE_SIZE"] = 10

        # Write.
        self.f.write(b"12345678901")
        self.assertFalse(self.f.in_memory)

        # Assert that the file exists
        self.assertEqual(self.f.actual_file_name, b"foo")
        self.assert_exists()

    def test_file_full_name_with_ext(self):
        self.c["UPLOAD_DIR"] = self.d
        self.c["UPLOAD_KEEP_FILENAME"] = True
        self.c["UPLOAD_KEEP_EXTENSIONS"] = True
        self.c["MAX_MEMORY_FILE_SIZE"] = 10

        # Write.
        self.f.write(b"12345678901")
        self.assertFalse(self.f.in_memory)

        # Assert that the file exists
        self.assertEqual(self.f.actual_file_name, b"foo.txt")
        self.assert_exists()

    def test_no_dir_with_extension(self):
        self.c["UPLOAD_KEEP_EXTENSIONS"] = True
        self.c["MAX_MEMORY_FILE_SIZE"] = 10

        # Write.
        self.f.write(b"12345678901")
        self.assertFalse(self.f.in_memory)

        # Assert that the file exists
        ext = os.path.splitext(self.f.actual_file_name)[1]
        self.assertEqual(ext, b".txt")
        self.assert_exists()

    def test_invalid_dir_with_name(self):
        # Write to this dir.
        self.c["UPLOAD_DIR"] = force_bytes(os.path.join("/", "tmp", "notexisting"))
        self.c["UPLOAD_KEEP_FILENAME"] = True
        self.c["MAX_MEMORY_FILE_SIZE"] = 5

        # Write.
        with self.assertRaises(FileError):
            self.f.write(b"1234567890")

    def test_invalid_dir_no_name(self):
        # Write to this dir.
        self.c["UPLOAD_DIR"] = force_bytes(os.path.join("/", "tmp", "notexisting"))
        self.c["UPLOAD_KEEP_FILENAME"] = False
        self.c["MAX_MEMORY_FILE_SIZE"] = 5

        # Write.
        with self.assertRaises(FileError):
            self.f.write(b"1234567890")

    # TODO: test uploading two files with the same name.


class TestParseOptionsHeader(unittest.TestCase):
    def test_simple(self):
        t, p = parse_options_header("application/json")
        self.assertEqual(t, b"application/json")
        self.assertEqual(p, {})

    def test_blank(self):
        t, p = parse_options_header("")
        self.assertEqual(t, b"")
        self.assertEqual(p, {})

    def test_single_param(self):
        t, p = parse_options_header("application/json;par=val")
        self.assertEqual(t, b"application/json")
        self.assertEqual(p, {b"par": b"val"})

    def test_single_param_with_spaces(self):
        t, p = parse_options_header(b"application/json;     par=val")
        self.assertEqual(t, b"application/json")
        self.assertEqual(p, {b"par": b"val"})

    def test_multiple_params(self):
        t, p = parse_options_header(b"application/json;par=val;asdf=foo")
        self.assertEqual(t, b"application/json")
        self.assertEqual(p, {b"par": b"val", b"asdf": b"foo"})

    def test_quoted_param(self):
        t, p = parse_options_header(b'application/json;param="quoted"')
        self.assertEqual(t, b"application/json")
        self.assertEqual(p, {b"param": b"quoted"})

    def test_quoted_param_with_semicolon(self):
        t, p = parse_options_header(b'application/json;param="quoted;with;semicolons"')
        self.assertEqual(p[b"param"], b"quoted;with;semicolons")

    def test_quoted_param_with_escapes(self):
        t, p = parse_options_header(
            b'application/json;param="This \\" is \\" a \\" quote"'
        )
        self.assertEqual(p[b"param"], b'This " is " a " quote')

    def test_handles_ie6_bug(self):
        t, p = parse_options_header(
            b'text/plain; filename="C:\\this\\is\\a\\path\\file.txt"'
        )

        self.assertEqual(p[b"filename"], b"file.txt")


class TestBaseParser(unittest.TestCase):
    def setUp(self):
        self.b = BaseParser()
        self.b.callbacks = {}

    def test_callbacks(self):
        # The stupid list-ness is to get around lack of nonlocal on py2
        length = [0]

        def on_foo():
            length[0] += 1

        self.b.set_callback("foo", on_foo)
        self.b.callback("foo")
        self.assertEqual(length[0], 1)

        self.b.set_callback("foo", None)
        self.b.callback("foo")
        self.assertEqual(length[0], 1)


class TestQuerystringParser(unittest.TestCase):
    def assert_fields(self, *args, **kwargs):
        if kwargs.pop("finalize", True):
            self.p.finalize()

        self.assertEqual(self.f, list(args))
        if kwargs.get("reset", True):
            self.f = []

    def setUp(self):
        self.reset()

    def reset(self):
        self.f = []

        name_buffer = []
        data_buffer = []

        def on_field_name(data, start, end):
            name_buffer.append(data[start:end])

        def on_field_data(data, start, end):
            data_buffer.append(data[start:end])

        def on_field_end():
            self.f.append((b"".join(name_buffer), b"".join(data_buffer)))

            del name_buffer[:]
            del data_buffer[:]

        callbacks = {
            "on_field_name": on_field_name,
            "on_field_data": on_field_data,
            "on_field_end": on_field_end,
        }

        self.p = QuerystringParser(callbacks)

    def test_simple_querystring(self):
        self.p.write(b"foo=bar")

        self.assert_fields((b"foo", b"bar"))

    def test_querystring_blank_beginning(self):
        self.p.write(b"&foo=bar")

        self.assert_fields((b"foo", b"bar"))

    def test_querystring_blank_end(self):
        self.p.write(b"foo=bar&")

        self.assert_fields((b"foo", b"bar"))

    def test_multiple_querystring(self):
        self.p.write(b"foo=bar&asdf=baz")

        self.assert_fields((b"foo", b"bar"), (b"asdf", b"baz"))

    def test_streaming_simple(self):
        self.p.write(b"foo=bar&")
        self.assert_fields((b"foo", b"bar"), finalize=False)

        self.p.write(b"asdf=baz")
        self.assert_fields((b"asdf", b"baz"))

    def test_streaming_break(self):
        self.p.write(b"foo=one")
        self.assert_fields(finalize=False)

        self.p.write(b"two")
        self.assert_fields(finalize=False)

        self.p.write(b"three")
        self.assert_fields(finalize=False)

        self.p.write(b"&asd")
        self.assert_fields((b"foo", b"onetwothree"), finalize=False)

        self.p.write(b"f=baz")
        self.assert_fields((b"asdf", b"baz"))

    def test_semicolon_seperator(self):
        self.p.write(b"foo=bar;asdf=baz")

        self.assert_fields((b"foo", b"bar"), (b"asdf", b"baz"))

    def test_too_large_field(self):
        self.p.max_size = 15

        # Note: len = 8
        self.p.write(b"foo=bar&")
        self.assert_fields((b"foo", b"bar"), finalize=False)

        # Note: len = 8, only 7 bytes processed
        self.p.write(b"a=123456")
        self.assert_fields((b"a", b"12345"))

    def test_invalid_max_size(self):
        with self.assertRaises(ValueError):
            QuerystringParser(max_size=-100)

    def test_strict_parsing_pass(self):
        data = b"foo=bar&another=asdf"
        for first, last in split_all(data):
            self.reset()
            self.p.strict_parsing = True

            # print("%r / %r" % (first, last))

            self.p.write(first)
            self.p.write(last)
            self.assert_fields((b"foo", b"bar"), (b"another", b"asdf"))

    def test_strict_parsing_fail_double_sep(self):
        data = b"foo=bar&&another=asdf"
        for first, last in split_all(data):
            self.reset()
            self.p.strict_parsing = True

            cnt = 0
            with self.assertRaises(QuerystringParseError) as cm:
                cnt += self.p.write(first)
                cnt += self.p.write(last)
                self.p.finalize()

            # The offset should occur at 8 bytes into the data (as a whole),
            # so we calculate the offset into the chunk.
            if cm is not None:
                self.assertEqual(cm.exception.offset, 8 - cnt)

    def test_double_sep(self):
        data = b"foo=bar&&another=asdf"
        for first, last in split_all(data):
            # print(" %r / %r " % (first, last))
            self.reset()

            cnt = 0
            cnt += self.p.write(first)
            cnt += self.p.write(last)

            self.assert_fields((b"foo", b"bar"), (b"another", b"asdf"))

    def test_strict_parsing_fail_no_value(self):
        self.p.strict_parsing = True
        with self.assertRaises(QuerystringParseError) as cm:
            self.p.write(b"foo=bar&blank&another=asdf")

        if cm is not None:
            self.assertEqual(cm.exception.offset, 8)

    def test_success_no_value(self):
        self.p.write(b"foo=bar&blank&another=asdf")
        self.assert_fields((b"foo", b"bar"), (b"blank", b""), (b"another", b"asdf"))


class TestBase64Decoder(unittest.TestCase):
    # Note: base64('foobar') == 'Zm9vYmFy'
    def setUp(self):
        self.f = BytesIO()
        self.d = Base64Decoder(self.f)

    def assert_data(self, data, finalize=True):
        if finalize:
            self.d.finalize()

        self.f.seek(0)
        self.assertEqual(self.f.read(), data)
        self.f.seek(0)
        self.f.truncate()

    def test_simple(self):
        self.d.write(b"Zm9vYmFy")
        self.assert_data(b"foobar")

    def test_bad(self):
        with self.assertRaises(DecodeError):
            self.d.write(b"Zm9v!mFy")

    def test_split_properly(self):
        self.d.write(b"Zm9v")
        self.d.write(b"YmFy")
        self.assert_data(b"foobar")

    def test_bad_split(self):
        buff = b"Zm9v"
        for i in range(1, 4):
            first, second = buff[:i], buff[i:]

            self.setUp()
            self.d.write(first)
            self.d.write(second)
            self.assert_data(b"foo")

    def test_long_bad_split(self):
        buff = b"Zm9vYmFy"
        for i in range(5, 8):
            first, second = buff[:i], buff[i:]

            self.setUp()
            self.d.write(first)
            self.d.write(second)
            self.assert_data(b"foobar")

    def test_close_and_finalize(self):
        parser = Mock()
        f = Base64Decoder(parser)

        f.finalize()
        parser.finalize.assert_called_once_with()

        f.close()
        parser.close.assert_called_once_with()

    def test_bad_length(self):
        self.d.write(b"Zm9vYmF")  # missing ending 'y'

        with self.assertRaises(DecodeError):
            self.d.finalize()


class TestQuotedPrintableDecoder(unittest.TestCase):
    def setUp(self):
        self.f = BytesIO()
        self.d = QuotedPrintableDecoder(self.f)

    def assert_data(self, data, finalize=True):
        if finalize:
            self.d.finalize()

        self.f.seek(0)
        self.assertEqual(self.f.read(), data)
        self.f.seek(0)
        self.f.truncate()

    def test_simple(self):
        self.d.write(b"foobar")
        self.assert_data(b"foobar")

    def test_with_escape(self):
        self.d.write(b"foo=3Dbar")
        self.assert_data(b"foo=bar")

    def test_with_newline_escape(self):
        self.d.write(b"foo=\r\nbar")
        self.assert_data(b"foobar")

    def test_with_only_newline_escape(self):
        self.d.write(b"foo=\nbar")
        self.assert_data(b"foobar")

    def test_with_split_escape(self):
        self.d.write(b"foo=3")
        self.d.write(b"Dbar")
        self.assert_data(b"foo=bar")

    def test_with_split_newline_escape_1(self):
        self.d.write(b"foo=\r")
        self.d.write(b"\nbar")
        self.assert_data(b"foobar")

    def test_with_split_newline_escape_2(self):
        self.d.write(b"foo=")
        self.d.write(b"\r\nbar")
        self.assert_data(b"foobar")

    def test_close_and_finalize(self):
        parser = Mock()
        f = QuotedPrintableDecoder(parser)

        f.finalize()
        parser.finalize.assert_called_once_with()

        f.close()
        parser.close.assert_called_once_with()

    def test_not_aligned(self):
        """
        https://github.com/andrew-d/python-multipart/issues/6
        """
        self.d.write(b"=3AX")
        self.assert_data(b":X")

        # Additional offset tests
        self.d.write(b"=3")
        self.d.write(b"AX")
        self.assert_data(b":X")

        self.d.write(b"q=3AX")
        self.assert_data(b"q:X")


# Load our list of HTTP test cases.
http_tests_dir = os.path.join(curr_dir, "test_data", "http")

# Read in all test cases and load them.
NON_PARAMETRIZED_TESTS = set(["single_field_blocks"])
http_tests = []
for f in os.listdir(http_tests_dir):
    # Only load the HTTP test cases.
    fname, ext = os.path.splitext(f)
    if fname in NON_PARAMETRIZED_TESTS:
        continue

    if ext == ".http":
        # Get the YAML file and load it too.
        yaml_file = os.path.join(http_tests_dir, fname + ".yaml")

        # Load both.
        with open(os.path.join(http_tests_dir, f), "rb") as fd:
            test_data = fd.read()

        with open(yaml_file, "rb") as fd:
            yaml_data = yaml.load(fd)

        http_tests.append({"name": fname, "test": test_data, "result": yaml_data})


def split_all(val):
    """
    This function will split an array all possible ways.  For example:
        split_all([1,2,3,4])
    will give:
        ([1], [2,3,4]), ([1,2], [3,4]), ([1,2,3], [4])
    """
    for i in range(1, len(val) - 1):
        yield (val[:i], val[i:])


class FormParser:
    """This class is the all-in-one form parser.  Given all the information
    necessary to parse a form, it will instantiate the correct parser, create
    the proper :class:`Field` and :class:`File` classes to store the data that
    is parsed, and call the two given callbacks with each field and file as
    they become available.

    :param content_type: The Content-Type of the incoming request.  This is
                         used to select the appropriate parser.

    :param on_field: The callback to call when a field has been parsed and is
                     ready for usage.  See above for parameters.

    :param on_file: The callback to call when a file has been parsed and is
                    ready for usage.  See above for parameters.

    :param on_end: An optional callback to call when all fields and files in a
                   request has been parsed.  Can be None.

    :param boundary: If the request is a multipart/form-data request, this
                     should be the boundary of the request, as given in the
                     Content-Type header, as a bytestring.

    :param file_name: If the request is of type application/octet-stream, then
                      the body of the request will not contain any information
                      about the uploaded file.  In such cases, you can provide
                      the file name of the uploaded file manually.

    :param FileClass: The class to use for uploaded files.  Defaults to
                      :class:`File`, but you can provide your own class if you
                      wish to customize behaviour.  The class will be
                      instantiated as FileClass(file_name, field_name), and it
                      must provide the folllowing functions::
                          file_instance.write(data)
                          file_instance.finalize()
                          file_instance.close()

    :param FieldClass: The class to use for uploaded fields.  Defaults to
                       :class:`Field`, but you can provide your own class if
                       you wish to customize behaviour.  The class will be
                       instantiated as FieldClass(field_name), and it must
                       provide the folllowing functions::
                           field_instance.write(data)
                           field_instance.finalize()
                           field_instance.close()

    :param config: Configuration to use for this FormParser.  The default
                   values are taken from the DEFAULT_CONFIG value, and then
                   any keys present in this dictionary will overwrite the
                   default values.

    """

    #: This is the default configuration for our form parser.
    #: Note: all file sizes should be in bytes.
    DEFAULT_CONFIG = {
        "MAX_BODY_SIZE": float("inf"),
        "MAX_MEMORY_FILE_SIZE": 1 * 1024 * 1024,
        "UPLOAD_DIR": None,
        "UPLOAD_KEEP_FILENAME": False,
        "UPLOAD_KEEP_EXTENSIONS": False,
        # Error on invalid Content-Transfer-Encoding?
        "UPLOAD_ERROR_ON_BAD_CTE": False,
    }

    def __init__(
        self,
        content_type,
        on_field,
        on_file,
        on_end=None,
        boundary=None,
        file_name=None,
        FileClass=File,
        FieldClass=Field,
        config={},
    ):
        import logging

        self.logger = logging.getLogger(__name__)

        # Save variables.
        self.content_type = content_type
        self.boundary = boundary
        self.bytes_received = 0
        self.parser = None

        # Save callbacks.
        self.on_field = on_field
        self.on_file = on_file
        self.on_end = on_end

        # Save classes.
        self.FileClass = File
        self.FieldClass = Field

        # Set configuration options.
        self.config = self.DEFAULT_CONFIG.copy()
        self.config.update(config)

        if (
            content_type == "application/x-www-form-urlencoded"
            or content_type == "application/x-url-encoded"
        ):

            name_buffer = []

            class vars(object):
                f = None

            def on_field_start():
                pass

            def on_field_name(data, start, end):
                name_buffer.append(data[start:end])

            def on_field_data(data, start, end):
                if vars.f is None:
                    vars.f = FieldClass(b"".join(name_buffer))
                    del name_buffer[:]
                vars.f.write(data[start:end])

            def on_field_end():
                # Finalize and call callback.
                if vars.f is None:
                    # If we get here, it's because there was no field data.
                    # We create a field, set it to None, and then continue.
                    vars.f = FieldClass(b"".join(name_buffer))
                    del name_buffer[:]
                    vars.f.set_none()

                vars.f.finalize()
                on_field(vars.f)
                vars.f = None

            def on_end():
                if self.on_end is not None:
                    self.on_end()

            # Setup callbacks.
            callbacks = {
                "on_field_start": on_field_start,
                "on_field_name": on_field_name,
                "on_field_data": on_field_data,
                "on_field_end": on_field_end,
                "on_end": on_end,
            }

            # Instantiate parser.
            parser = QuerystringParser(
                callbacks=callbacks, max_size=self.config["MAX_BODY_SIZE"]
            )

        elif content_type == "multipart/form-data":
            if boundary is None:
                self.logger.error("No boundary given")
                raise FormParserError("No boundary given")

            header_name = []
            header_value = []
            headers = {}

            # No 'nonlocal' on Python 2 :-(
            class vars(object):
                f = None
                writer = None
                is_file = False

            def on_part_begin():
                pass

            def on_part_data(data, start, end):
                bytes_processed = vars.writer.write(data[start:end])
                # TODO: check for error here.
                return bytes_processed

            def on_part_end():
                vars.f.finalize()
                if vars.is_file:
                    on_file(vars.f)
                else:
                    on_field(vars.f)

            def on_header_field(data, start, end):
                header_name.append(data[start:end])

            def on_header_value(data, start, end):
                header_value.append(data[start:end])

            def on_header_end():
                headers[b"".join(header_name)] = b"".join(header_value)
                del header_name[:]
                del header_value[:]

            def on_headers_finished():
                # Reset the 'is file' flag.
                vars.is_file = False

                # Parse the content-disposition header.
                # TODO: handle mixed case
                content_disp = headers.get(b"Content-Disposition")
                disp, options = parse_options_header(content_disp)

                # Get the field and filename.
                field_name = options.get(b"name")
                file_name = options.get(b"filename")
                # TODO: check for errors

                # Create the proper class.
                if file_name is None:
                    vars.f = FieldClass(field_name)
                else:
                    vars.f = FileClass(file_name, field_name, config=self.config)
                    vars.is_file = True

                # Parse the given Content-Transfer-Encoding to determine what
                # we need to do with the incoming data.
                # TODO: check that we properly handle 8bit / 7bit encoding.
                transfer_encoding = headers.get(b"Content-Transfer-Encoding", b"7bit")

                if (
                    transfer_encoding == b"binary"
                    or transfer_encoding == b"8bit"
                    or transfer_encoding == b"7bit"
                ):
                    vars.writer = vars.f

                elif transfer_encoding == b"base64":
                    vars.writer = Base64Decoder(vars.f)

                elif transfer_encoding == b"quoted-printable":
                    vars.writer = QuotedPrintableDecoder(vars.f)

                else:
                    self.logger.warning(
                        "Unknown Content-Transfer-Encoding: " "%r", transfer_encoding
                    )
                    if self.config["UPLOAD_ERROR_ON_BAD_CTE"]:
                        raise FormParserError(
                            'Unknown Content-Transfer-Encoding "{0}"'.format(
                                transfer_encoding
                            )
                        )
                    else:
                        # If we aren't erroring, then we just treat this as an
                        # unencoded Content-Transfer-Encoding.
                        vars.writer = vars.f

            def on_end():
                vars.writer.finalize()
                if self.on_end is not None:
                    self.on_end()

            # These are our callbacks for the parser.
            callbacks = {
                "on_part_begin": on_part_begin,
                "on_part_data": on_part_data,
                "on_part_end": on_part_end,
                "on_header_field": on_header_field,
                "on_header_value": on_header_value,
                "on_header_end": on_header_end,
                "on_headers_finished": on_headers_finished,
                "on_end": on_end,
            }

            # Instantiate a multipart parser.
            parser = MultipartParser(
                boundary, callbacks, max_size=self.config["MAX_BODY_SIZE"]
            )

        else:
            self.logger.warning("Unknown Content-Type: %r", content_type)
            raise FormParserError("Unknown Content-Type: {0}".format(content_type))

        self.parser = parser

    def write(self, data):
        """Write some data.  The parser will forward this to the appropriate
        underlying parser.

        :param data: a bytestring
        """
        self.bytes_received += len(data)
        # TODO: check the parser's return value for errors?
        return self.parser.write(data)

    def finalize(self):
        """Finalize the parser."""
        if self.parser is not None and hasattr(self.parser, "finalize"):
            self.parser.finalize()

    def close(self):
        """Close the parser."""
        if self.parser is not None and hasattr(self.parser, "close"):
            self.parser.close()

    def __repr__(self):
        return "%s(content_type=%r, parser=%r)" % (
            self.__class__.__name__,
            self.content_type,
            self.parser,
        )


class TestFormParser(unittest.TestCase):
    def make(self, boundary, config={}):
        self.ended = False
        self.files = []
        self.fields = []

        def on_field(f):
            self.fields.append(f)

        def on_file(f):
            self.files.append(f)

        def on_end():
            self.ended = True

        # Get a form-parser instance.
        self.f = FormParser(
            "multipart/form-data",
            on_field,
            on_file,
            on_end,
            boundary=boundary,
            config=config,
        )

    def assert_file_data(self, f, data):
        o = f.file_object
        o.seek(0)
        file_data = o.read()
        self.assertEqual(file_data, data)

    def assert_file(self, field_name, file_name, data):
        # Find this file.
        found = None
        for f in self.files:
            if f.field_name == field_name:
                found = f
                break

        # Assert that we found it.
        self.assertIsNotNone(found)

        try:
            # Assert about this file.
            self.assert_file_data(found, data)
            self.assertEqual(found.file_name, file_name)

            # Remove it from our list.
            self.files.remove(found)
        finally:
            # Close our file
            found.close()

    def assert_field(self, name, value):
        # Find this field in our fields list.
        found = None
        for f in self.fields:
            if f.field_name == name:
                found = f
                break

        # Assert that it exists and matches.
        self.assertIsNotNone(found)
        self.assertEqual(value, found.value)

        # Remove it for future iterations.
        self.fields.remove(found)

    def test_http(self):
        for param in http_tests:
            # Firstly, create our parser with the given boundary.
            boundary = param["result"]["boundary"]
            if isinstance(boundary, str):
                boundary = boundary.encode("latin-1")
            self.make(boundary)

            # Now, we feed the parser with data.
            exc = None
            try:
                processed = self.f.write(param["test"])
                self.f.finalize()
            except MultipartParseError as _:
                processed = 0
                exc = _

            # print(repr(param))
            # print("")
            # print(repr(self.fields))
            # print(repr(self.files))

            # Do we expect an error?
            if "error" in param["result"]["expected"]:
                self.assertIsNotNone(exc)
                self.assertEqual(param["result"]["expected"]["error"], exc.offset)
                return

            # No error!
            self.assertEqual(processed, len(param["test"]))

            # Assert that the parser gave us the appropriate fields/files.
            for e in param["result"]["expected"]:
                # Get our type and name.
                type = e["type"]
                name = e["name"].encode("latin-1")

                if type == "field":
                    self.assert_field(name, e["data"])

                elif type == "file":
                    self.assert_file(name, e["file_name"].encode("latin-1"), e["data"])

                else:
                    assert False

    def test_random_splitting(self):
        """
        This test runs a simple multipart body with one field and one file
        through every possible split.
        """
        # Load test data.
        test_file = "single_field_single_file.http"
        with open(os.path.join(http_tests_dir, test_file), "rb") as f:
            test_data = f.read()

        # We split the file through all cases.
        for first, last in split_all(test_data):
            # Create form parser.
            self.make("boundary")

            # Feed with data in 2 chunks.
            i = 0
            i += self.f.write(first)
            i += self.f.write(last)
            self.f.finalize()

            # Assert we processed everything.
            self.assertEqual(i, len(test_data))

            # Assert that our file and field are here.
            self.assert_field(b"field", b"test1")
            self.assert_file(b"file", b"file.txt", b"test2")

    def test_feed_single_bytes(self):
        """
        This test parses a simple multipart body 1 byte at a time.
        """
        # Load test data.
        test_file = "single_field_single_file.http"
        with open(os.path.join(http_tests_dir, test_file), "rb") as f:
            test_data = f.read()

        # Create form parser.
        self.make("boundary")

        # Write all bytes.
        # NOTE: Can't simply do `for b in test_data`, since that gives
        # an integer when iterating over a bytes object on Python 3.
        i = 0
        for x in range(len(test_data)):
            b = test_data[x : x + 1]
            i += self.f.write(b)

        self.f.finalize()

        # Assert we processed everything.
        self.assertEqual(i, len(test_data))

        # Assert that our file and field are here.
        self.assert_field(b"field", b"test1")
        self.assert_file(b"file", b"file.txt", b"test2")

    def test_feed_blocks(self):
        """
        This test parses a simple multipart body 1 byte at a time.
        """
        # Load test data.
        test_file = "single_field_blocks.http"
        with open(os.path.join(http_tests_dir, test_file), "rb") as f:
            test_data = f.read()

        for c in range(1, len(test_data) + 1):
            # Skip first `d` bytes - not interesting
            for d in range(c):

                # Create form parser.
                self.make("boundary")
                # Skip
                i = 0
                self.f.write(test_data[:d])
                i += d
                for x in range(d, len(test_data), c):
                    # Write a chunk to achieve condition
                    #     `i == data_length - 1`
                    # in boundary search loop (multipatr.py:1302)
                    b = test_data[x : x + c]
                    i += self.f.write(b)

                self.f.finalize()

                # Assert we processed everything.
                self.assertEqual(i, len(test_data))

                # Assert that our field is here.
                self.assert_field(b"field", b"0123456789ABCDEFGHIJ0123456789ABCDEFGHIJ")

    def test_request_body_fuzz(self):
        """
        This test randomly fuzzes the request body to ensure that no strange
        exceptions are raised and we don't end up in a strange state.  The
        fuzzing consists of randomly doing one of the following:
            - Adding a random byte at a random offset
            - Randomly deleting a single byte
            - Randomly swapping two bytes
        """
        # Load test data.
        test_file = "single_field_single_file.http"
        with open(os.path.join(http_tests_dir, test_file), "rb") as f:
            test_data = f.read()

        iterations = 1000
        successes = 0
        failures = 0
        exceptions = 0

        # print("Running %d iterations of fuzz testing:" % (iterations,))
        for i in range(iterations):
            # Create a bytearray to mutate.
            fuzz_data = bytearray(test_data)

            # Pick what we're supposed to do.
            choice = random.choice([1, 2, 3])
            if choice == 1:
                # Add a random byte.
                i = random.randrange(len(test_data))
                b = random.randrange(256)

                fuzz_data.insert(i, b)
                # msg = "Inserting byte %r at offset %d" % (b, i)

            elif choice == 2:
                # Remove a random byte.
                i = random.randrange(len(test_data))
                del fuzz_data[i]

                # msg = "Deleting byte at offset %d" % (i,)

            elif choice == 3:
                # Swap two bytes.
                i = random.randrange(len(test_data) - 1)
                fuzz_data[i], fuzz_data[i + 1] = fuzz_data[i + 1], fuzz_data[i]

                # msg = "Swapping bytes %d and %d" % (i, i + 1)

            # Print message, so if this crashes, we can inspect the output.
            # print("  " + msg)

            # Create form parser.
            self.make("boundary")

            # Feed with data, and ignore form parser exceptions.
            i = 0
            try:
                i = self.f.write(bytes(fuzz_data))
                self.f.finalize()
            except FormParserError:
                exceptions += 1
            else:
                if i == len(fuzz_data):
                    successes += 1
                else:
                    failures += 1

        # print("--------------------------------------------------")
        # print("Successes:  %d" % (successes,))
        # print("Failures:   %d" % (failures,))
        # print("Exceptions: %d" % (exceptions,))

    def test_request_body_fuzz_random_data(self):
        """
        This test will fuzz the multipart parser with some number of iterations
        of randomly-generated data.
        """
        iterations = 1000
        successes = 0
        failures = 0
        exceptions = 0

        # print("Running %d iterations of fuzz testing:" % (iterations,))
        for i in range(iterations):
            data_size = random.randrange(100, 4096)
            data = os.urandom(data_size)
            # print("  Testing with %d random bytes..." % (data_size,))

            # Create form parser.
            self.make("boundary")

            # Feed with data, and ignore form parser exceptions.
            i = 0
            try:
                i = self.f.write(bytes(data))
                self.f.finalize()
            except FormParserError:
                exceptions += 1
            else:
                if i == len(data):
                    successes += 1
                else:
                    failures += 1

        # print("--------------------------------------------------")
        # print("Successes:  %d" % (successes,))
        # print("Failures:   %d" % (failures,))
        # print("Exceptions: %d" % (exceptions,))

    def test_bad_start_boundary(self):
        self.make("boundary")
        data = b"--boundary\rfoobar"
        with self.assertRaises(MultipartParseError):
            self.f.write(data)

        self.make("boundary")
        data = b"--boundaryfoobar"
        with self.assertRaises(MultipartParseError):
            self.f.write(data)

    def test_querystring(self):
        fields = []

        def on_field(f):
            fields.append(f)

        on_file = Mock()
        on_end = Mock()

        def simple_test(f):
            # Reset tracking.
            del fields[:]
            on_file.reset_mock()
            on_end.reset_mock()

            # Write test data.
            f.write(b"foo=bar")
            f.write(b"&test=asdf")
            f.finalize()

            # Assert we only recieved 2 fields...
            self.assertFalse(on_file.called)
            self.assertEqual(len(fields), 2)

            # ...assert that we have the correct data...
            self.assertEqual(fields[0].field_name, b"foo")
            self.assertEqual(fields[0].value, b"bar")

            self.assertEqual(fields[1].field_name, b"test")
            self.assertEqual(fields[1].value, b"asdf")

            # ... and assert that we've finished.
            self.assertTrue(on_end.called)

        f = FormParser(
            "application/x-www-form-urlencoded", on_field, on_file, on_end=on_end
        )
        self.assertTrue(isinstance(f.parser, QuerystringParser))
        simple_test(f)

        f = FormParser("application/x-url-encoded", on_field, on_file, on_end=on_end)
        self.assertTrue(isinstance(f.parser, QuerystringParser))
        simple_test(f)

    def test_close_methods(self):
        parser = Mock()
        f = FormParser("application/x-url-encoded", None, None)
        f.parser = parser

        f.finalize()
        parser.finalize.assert_called_once_with()

        f.close()
        parser.close.assert_called_once_with()

    def test_bad_content_type(self):
        # We should raise a ValueError for a bad Content-Type
        with self.assertRaises(ValueError):
            FormParser("application/bad", None, None)

    def test_no_boundary_given(self):
        # We should raise a FormParserError when parsing a multipart message
        # without a boundary.
        with self.assertRaises(FormParserError):
            FormParser("multipart/form-data", None, None)

    def test_bad_content_transfer_encoding(self):
        data = b'----boundary\r\nContent-Disposition: form-data; name="file"; filename="test.txt"\r\nContent-Type: text/plain\r\nContent-Transfer-Encoding: badstuff\r\n\r\nTest\r\n----boundary--\r\n'

        files = []

        def on_file(f):
            files.append(f)

        on_field = Mock()
        on_end = Mock()

        # Test with erroring.
        config = {"UPLOAD_ERROR_ON_BAD_CTE": True}
        f = FormParser(
            "multipart/form-data",
            on_field,
            on_file,
            on_end=on_end,
            boundary="--boundary",
            config=config,
        )

        with self.assertRaises(FormParserError):
            f.write(data)
            f.finalize()

        # Test without erroring.
        config = {"UPLOAD_ERROR_ON_BAD_CTE": False}
        f = FormParser(
            "multipart/form-data",
            on_field,
            on_file,
            on_end=on_end,
            boundary="--boundary",
            config=config,
        )

        f.write(data)
        f.finalize()
        self.assert_file_data(files[0], b"Test")

    def test_handles_None_fields(self):
        fields = []

        def on_field(f):
            fields.append(f)

        on_file = Mock()
        on_end = Mock()

        f = FormParser(
            "application/x-www-form-urlencoded", on_field, on_file, on_end=on_end
        )
        f.write(b"foo=bar&another&baz=asdf")
        f.finalize()

        self.assertEqual(fields[0].field_name, b"foo")
        self.assertEqual(fields[0].value, b"bar")

        self.assertEqual(fields[1].field_name, b"another")
        self.assertEqual(fields[1].value, None)

        self.assertEqual(fields[2].field_name, b"baz")
        self.assertEqual(fields[2].value, b"asdf")

    def test_max_size_multipart(self):
        # Load test data.
        test_file = "single_field_single_file.http"
        with open(os.path.join(http_tests_dir, test_file), "rb") as f:
            test_data = f.read()

        # Create form parser.
        self.make("boundary")

        # Set the maximum length that we can process to be halfway through the
        # given data.
        self.f.parser.max_size = len(test_data) / 2

        i = self.f.write(test_data)
        self.f.finalize()

        # Assert we processed the correct amount.
        self.assertEqual(i, len(test_data) / 2)

    def test_max_size_form_parser(self):
        # Load test data.
        test_file = "single_field_single_file.http"
        with open(os.path.join(http_tests_dir, test_file), "rb") as f:
            test_data = f.read()

        # Create form parser setting the maximum length that we can process to
        # be halfway through the given data.
        size = len(test_data) / 2
        self.make("boundary", config={"MAX_BODY_SIZE": size})

        i = self.f.write(test_data)
        self.f.finalize()

        # Assert we processed the correct amount.
        self.assertEqual(i, len(test_data) / 2)

    def test_invalid_max_size_multipart(self):
        with self.assertRaises(ValueError):
            MultipartParser(b"bound", max_size="foo")


class ForceMultipartDict(dict):
    def __bool__(self):
        return True


# FORCE_MULTIPART is an empty dict that boolean-evaluates as `True`.
FORCE_MULTIPART = ForceMultipartDict()


async def app(scope, receive, send):
    request = Request(scope, receive)
    data = await request.form
    output = {}
    for key, value in data.items():
        if isinstance(value, UploadFile):
            content = await value.read()
            output[key] = {
                "filename": value.filename,
                "content": content.decode(),
                "content_type": value.content_type,
            }
        else:
            output[key] = value
    await request.close()
    response = JSONResponse(output)
    await response(scope, receive, send)


async def multi_items_app(scope, receive, send):
    request = Request(scope, receive)
    data = await request.form
    output = {}
    for key, value in data.multi_items():
        if key not in output:
            output[key] = []
        if isinstance(value, UploadFile):
            content = await value.read()
            output[key].append(
                {
                    "filename": value.filename,
                    "content": content.decode(),
                    "content_type": value.content_type,
                }
            )
        else:
            output[key].append(value)
    await request.close()
    response = JSONResponse(output)
    await response(scope, receive, send)


async def app_read_body(scope, receive, send):
    request = Request(scope, receive)
    # Read bytes, to force request.stream() to return the already parsed body
    await request.body
    data = await request.form
    output = {}
    for key, value in data.items():
        output[key] = value
    await request.close()
    response = JSONResponse(output)
    await response(scope, receive, send)


def test_multipart_request_data(tmpdir):
    client = TestClient(app)
    response = client.post("/", data={"some": "data"}, files=FORCE_MULTIPART)
    assert response.json() == {"some": "data"}


def test_multipart_request_files(tmpdir):
    path = os.path.join(tmpdir, "test.txt")
    with open(path, "wb") as file:
        file.write(b"<file content>")

    client = TestClient(app)
    with open(path, "rb") as f:
        response = client.post("/", files={"test": f})
        assert response.json() == {
            "test": {
                "filename": "test.txt",
                "content": "<file content>",
                "content_type": "",
            }
        }


def test_multipart_request_files_with_content_type(tmpdir):
    path = os.path.join(tmpdir, "test.txt")
    with open(path, "wb") as file:
        file.write(b"<file content>")

    client = TestClient(app)
    with open(path, "rb") as f:
        response = client.post("/", files={"test": ("test.txt", f, "text/plain")})
        assert response.json() == {
            "test": {
                "filename": "test.txt",
                "content": "<file content>",
                "content_type": "text/plain",
            }
        }


def test_multipart_request_multiple_files(tmpdir):
    path1 = os.path.join(tmpdir, "test1.txt")
    with open(path1, "wb") as file:
        file.write(b"<file1 content>")

    path2 = os.path.join(tmpdir, "test2.txt")
    with open(path2, "wb") as file:
        file.write(b"<file2 content>")

    client = TestClient(app)
    with open(path1, "rb") as f1, open(path2, "rb") as f2:
        response = client.post(
            "/", files={"test1": f1, "test2": ("test2.txt", f2, "text/plain")}
        )
        assert response.json() == {
            "test1": {
                "filename": "test1.txt",
                "content": "<file1 content>",
                "content_type": "",
            },
            "test2": {
                "filename": "test2.txt",
                "content": "<file2 content>",
                "content_type": "text/plain",
            },
        }


def test_multi_items(tmpdir):
    path1 = os.path.join(tmpdir, "test1.txt")
    with open(path1, "wb") as file:
        file.write(b"<file1 content>")

    path2 = os.path.join(tmpdir, "test2.txt")
    with open(path2, "wb") as file:
        file.write(b"<file2 content>")

    client = TestClient(multi_items_app)
    with open(path1, "rb") as f1, open(path2, "rb") as f2:
        response = client.post(
            "/",
            data=[("test1", "abc")],
            files=[("test1", f1), ("test1", ("test2.txt", f2, "text/plain"))],
        )
        assert response.json() == {
            "test1": [
                "abc",
                {
                    "filename": "test1.txt",
                    "content": "<file1 content>",
                    "content_type": "",
                },
                {
                    "filename": "test2.txt",
                    "content": "<file2 content>",
                    "content_type": "text/plain",
                },
            ]
        }


def test_multipart_request_mixed_files_and_data(tmpdir):
    client = TestClient(app)
    response = client.post(
        "/",
        data=(
            # data
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
            b'Content-Disposition: form-data; name="field0"\r\n\r\n'
            b"value0\r\n"
            # file
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
            b'Content-Disposition: form-data; name="file"; filename="file.txt"\r\n'
            b"Content-Type: text/plain\r\n\r\n"
            b"<file content>\r\n"
            # data
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
            b'Content-Disposition: form-data; name="field1"\r\n\r\n'
            b"value1\r\n"
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c--\r\n"
        ),
        headers={
            "Content-Type": (
                "multipart/form-data; boundary=a7f7ac8d4e2e437c877bb7b8d7cc549c"
            )
        },
    )
    assert response.json() == {
        "file": {
            "filename": "file.txt",
            "content": "<file content>",
            "content_type": "text/plain",
        },
        "field0": "value0",
        "field1": "value1",
    }


def test_multipart_request_with_charset_for_filename(tmpdir):
    client = TestClient(app)
    response = client.post(
        "/",
        data=(
            # file
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
            b'Content-Disposition: form-data; name="file"; filename="\xe6\x96\x87\xe6\x9b\xb8.txt"\r\n'  # noqa: E501
            b"Content-Type: text/plain\r\n\r\n"
            b"<file content>\r\n"
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c--\r\n"
        ),
        headers={
            "Content-Type": (
                "multipart/form-data; charset=utf-8; "
                "boundary=a7f7ac8d4e2e437c877bb7b8d7cc549c"
            )
        },
    )
    assert response.json() == {
        "file": {
            "filename": "文書.txt",
            "content": "<file content>",
            "content_type": "text/plain",
        }
    }


def test_multipart_request_without_charset_for_filename(tmpdir):
    client = TestClient(app)
    response = client.post(
        "/",
        data=(
            # file
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
            b'Content-Disposition: form-data; name="file"; filename="\xe7\x94\xbb\xe5\x83\x8f.jpg"\r\n'  # noqa: E501
            b"Content-Type: image/jpeg\r\n\r\n"
            b"<file content>\r\n"
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c--\r\n"
        ),
        headers={
            "Content-Type": (
                "multipart/form-data; boundary=a7f7ac8d4e2e437c877bb7b8d7cc549c"
            )
        },
    )
    assert response.json() == {
        "file": {
            "filename": "画像.jpg",
            "content": "<file content>",
            "content_type": "image/jpeg",
        }
    }


def test_multipart_request_with_encoded_value(tmpdir):
    client = TestClient(app)
    response = client.post(
        "/",
        data=(
            b"--20b303e711c4ab8c443184ac833ab00f\r\n"
            b"Content-Disposition: form-data; "
            b'name="value"\r\n\r\n'
            b"Transf\xc3\xa9rer\r\n"
            b"--20b303e711c4ab8c443184ac833ab00f--\r\n"
        ),
        headers={
            "Content-Type": (
                "multipart/form-data; charset=utf-8; "
                "boundary=20b303e711c4ab8c443184ac833ab00f"
            )
        },
    )
    assert response.json() == {"value": "Transférer"}


def test_urlencoded_request_data(tmpdir):
    client = TestClient(app)
    response = client.post("/", data={"some": "data"})
    assert response.json() == {"some": "data"}


def test_no_request_data(tmpdir):
    client = TestClient(app)
    response = client.post("/")
    assert response.json() == {}


def test_urlencoded_percent_encoding(tmpdir):
    client = TestClient(app)
    response = client.post("/", data={"some": "da ta"})
    assert response.json() == {"some": "da ta"}


def test_urlencoded_percent_encoding_keys(tmpdir):
    client = TestClient(app)
    response = client.post("/", data={"so me": "data"})
    assert response.json() == {"so me": "data"}


def test_urlencoded_multi_field_app_reads_body(tmpdir):
    client = TestClient(app_read_body)
    response = client.post("/", data={"some": "data", "second": "key pair"})
    assert response.json() == {"some": "data", "second": "key pair"}


def test_multipart_multi_field_app_reads_body(tmpdir):
    client = TestClient(app_read_body)
    response = client.post(
        "/", data={"some": "data", "second": "key pair"}, files=FORCE_MULTIPART
    )
    assert response.json() == {"some": "data", "second": "key pair"}


def test_user_safe_decode_helper():
    result = _user_safe_decode(b"\xc4\x99\xc5\xbc\xc4\x87", "utf-8")
    assert result == "ężć"


def test_user_safe_decode_ignores_wrong_charset():
    result = _user_safe_decode(b"abc", "latin-8")
    assert result == "abc"
