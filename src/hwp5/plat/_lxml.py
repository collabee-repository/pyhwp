# -*- coding: utf-8 -*-
#
#   pyhwp : hwp file format parser in python
#   Copyright (C) 2010-2015 mete0r <mete0r@sarangbang.or.kr>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from contextlib import contextmanager
import io
import logging
import os.path
import shutil
import sys

from zope.interface import implementer

from ..errors import ImplementationNotAvailable
from ..errors import ValidationFailed
from ..interfaces import ITemporaryStreamFactory
from ..interfaces import IRelaxNG
from ..interfaces import IRelaxNGFactory
from ..interfaces import IXSLT
from ..interfaces import IXSLTFactory


PY3 = sys.version_info.major == 3


logger = logging.getLogger(__name__)


def is_available():
    try:
        from lxml import etree  # noqa
    except ImportError:
        return False
    else:
        return True


def is_enabled():
    try:
        from lxml import etree  # noqa
    except ImportError:
        return False
    else:
        return True


def createXSLTFactory(registry, **settings):
    try:
        import lxml  # noqa
    except ImportError:
        raise ImplementationNotAvailable('xslt/lxml')
    return XSLTFactory()


@implementer(IXSLTFactory)
class XSLTFactory:

    def xslt_from_file(self, xsl_path, **params):
        return XSLT(xsl_path, **params)


@implementer(IXSLT)
class XSLT:

    def __init__(self, xsl_path, **params):
        ''' Compile XSL Transform function.
        :param xsl_path: stylesheet path
        :returns: a transform function
        '''
        from lxml import etree

        with io.open(xsl_path, 'rb') as xsl_file:
            xsl_doc = etree.parse(xsl_file)

        self.xsl_path = xsl_path
        self.etree_xslt = etree.XSLT(xsl_doc)
        self.params = dict((name, etree.XSLT.strparam(value))
                           for name, value in params.items())

    def transform(self, input, output):
        '''
        >>> T.transform('input.xml', 'output.xml')
        '''
        with io.open(input, 'rb') as inp_file:
            with io.open(output, 'wb') as out_file:
                return self._transform(inp_file, out_file)

    def transform_into_stream(self, input, output):
        '''
        >>> T.transform_into_stream('input.xml', sys.stdout)
        '''
        with io.open(input, 'rb') as inp_file:
            return self._transform(inp_file, output)

    def _transform(self, input, output):
        # input, output: binary stream

        from lxml import etree
        source = etree.parse(input)
        logger.info('_lxml.xslt(%s) start',
                    os.path.basename(self.xsl_path))
        result = self.etree_xslt(source, **self.params)
        logger.info('_lxml.xslt(%s) end',
                    os.path.basename(self.xsl_path))
        # https://lxml.de/1.3/FAQ.html#what-is-the-difference-between-str-xslt-doc-and-xslt-doc-write
        result = bytes(result)
        output.write(result)
        return dict()


def createRelaxNGFactory(registry, **settings):
    try:
        import lxml  # noqa
    except ImportError:
        raise ImplementationNotAvailable('relaxng/lxml')
    temp_stream_factory = registry.getUtility(ITemporaryStreamFactory)
    return RelaxNGFactory(temp_stream_factory)


@implementer(IRelaxNGFactory)
class RelaxNGFactory:

    def __init__(self, temp_stream_factory):
        self.temp_stream_factory = temp_stream_factory

    def relaxng_validator_from_file(self, rng_path):
        return RelaxNG(self.temp_stream_factory, rng_path)


@implementer(IRelaxNG)
class RelaxNG:

    def __init__(self, temp_stream_factory, rng_path):
        from lxml import etree

        self.temp_stream_factory = temp_stream_factory

        with io.open(rng_path, 'rb') as rng_file:
            rng = etree.parse(rng_file)

        self.rng_path = rng_path
        self.etree_relaxng = etree.RelaxNG(rng)

    @contextmanager
    def validating_output(self, output):
        with self.temp_stream_factory.temporary_stream() as fp:
            yield fp
            fp.seek(0)
            if not self.validate_stream(fp):
                raise ValidationFailed('RelaxNG')
            fp.seek(0)
            shutil.copyfileobj(fp, output)

    def validate(self, input):
        from lxml import etree
        with io.open(input, 'rb') as f:
            doc = etree.parse(f)
        return self._validate(doc)

    def validate_stream(self, input):
        from lxml import etree
        doc = etree.parse(input)
        return self._validate(doc)

    def _validate(self, doc):
        logger.info('_lxml.relaxng(%s) start', os.path.basename(self.rng_path))
        try:
            valid = self.etree_relaxng.validate(doc)
        except Exception as e:
            logger.exception(e)
            raise
        else:
            if not valid:
                for error in self.etree_relaxng.error_log:
                    logger.error('%s', error)
            return valid
        finally:
            logger.info(
                '_lxml.relaxng(%s) end',
                os.path.basename(self.rng_path)
            )


def errlog_to_dict(error):
    return dict(message=error.message,
                filename=error.filename,
                line=error.line,
                column=error.column,
                domain=error.domain_name,
                type=error.type_name,
                level=error.level_name)
