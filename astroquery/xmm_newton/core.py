# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Elena Colomo
@contact: ecolomo@esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 3 Sept 2019


"""
from astroquery.utils import commons
from astropy import units
from astropy.units import Quantity
from astroquery.utils.tap.core import TapPlus
from astroquery.utils.tap.model import modelutils
from astroquery.query import BaseQuery
from astropy.table import Table
from six import BytesIO
import os
import re

from . import conf
from astropy import log


__all__ = ['XMMNewton', 'XMMNewtonClass']


class XMMNewtonHandler(BaseQuery):

    def __init__(self):
        super(XMMNewtonHandler, self).__init__()

    def get_file(self, filename, response, verbose=False):
        with open(filename, 'wb') as fh:
            fh.write(response.content)

        if os.pathsep not in filename:
            log.info("File {0} downloaded to current "
                     "directory".format(filename))
        else:
            log.info("File {0} downloaded".format(filename))

    def get_table(self, filename, response, output_format='votable',
                  verbose=False):
        with open(filename, 'wb') as fh:
            fh.write(response.content)

        table = modelutils.read_results_table_from_file(filename,
                                                        str(output_format))
        return table

    def request(self, t="GET", link=None, params=None,
                cache=None,
                timeout=None):
        return self._request(method=t, url=link,
                             params=params, cache=cache,
                             timeout=timeout)


Handler = XMMNewtonHandler()


class XMMNewtonClass(BaseQuery):

    data_url = conf.DATA_ACTION
    data_aio_url = conf.DATA_ACTION_AIO
    metadata_url = conf.METADATA_ACTION
    TIMEOUT = conf.TIMEOUT

    def __init__(self, url_handler=None, tap_handler=None):
        super(XMMNewtonClass, self).__init__()
        if url_handler is None:
            self._handler = Handler
        else:
            self._handler = url_handler

        if tap_handler is None:
            self._tap = TapPlus(url="http://nxsa.esac.esa.int"
                                    "/tap-server/tap/")
        else:
            self._tap = tap_handler

    def download_data(self, observation_id, verbose=False, **kwargs):
        """
        Download data from XMM-Newton

        Parameters
        ----------
        observation_id : string
            id of the observation to be downloaded, mandatory
            The identifier of the observation we want to retrieve, 10 digits
            example: 0144090201
        level : string
            level to download, optional, by default everything is downloaded
            values: ODF, PPS
        instname : string
            instrument name, optional, two characters, by default everything
            values: OM, R1, R2, M1, M2, PN
        instmode : string
            instrument mode, optional
            examples: Fast, FlatFieldLow, Image, PrimeFullWindow
        filter : string
            filter, optional
            examples: Closed, Open, Thick, UVM2, UVW1, UVW2, V
        expflag : string
            exposure flag, optional, by default everything
            values: S, U, X(not applicable)
        expno : integer
            exposure number with 3 digits, by default all exposures
            examples: 001, 003
        name : string
            product type, optional, 6 characters, by default all product types
            examples: 3COLIM, ATTTSR, EVENLI, SBSPEC, EXPMAP, SRCARF
        datasubsetno : character
            data subset number, optional, by default all
            examples: 0, 1
        sourceno : hex value
            source number, optional, by default all sources
            example: 00A, 021, 001
        extension : string
            file format, optional, by default all formats
            values: ASC, ASZ, FTZ, HTM, IND, PDF, PNG
        filename : string
            file name to be used to store the file, optional, default
            None
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        None. It downloads the observation indicated
        """

        link = self.data_aio_url + "obsno=" + observation_id

        link = link + "".join("&{key}={val}" for key, val in kwargs.items())

        response = self._handler.request('GET', link)
        if response is not None:
            response.raise_for_status()

            if filename is None:
                if "Content-Disposition" in response.headers.keys():
                    filename = re.findall('filename="(.+)"',
                                          response.headers[
                                              "Content-Disposition"])[0]
                else:
                    filename = observation_id + ".tar"

            self._handler.get_file(filename, response=response,
                                   verbose=verbose)

            if verbose:
                log.info("Wrote {0} to {1}".format(link, filename))

            return filename

    def get_postcard(self, observation_id, image_type="OBS_EPIC",
                     filename=None, verbose=False):
        """
        Download postcards from XSA

        Parameters
        ----------
        observation_id : string
            id of the observation for which download the postcard, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
        image_type : string
            image type, optional, default 'OBS_EPIC'
            The image_type to be returned. It can be: OBS_EPIC,
            OBS_RGS_FLUXED, OBS_RGS_FLUXED_2, OBS_RGS_FLUXED_3, OBS_EPIC_MT,
            OBS_RGS_FLUXED_MT, OBS_OM_V, OBS_OM_B, OBS_OM_U, OBS_OM_L,
            OBS_OM_M, OBS_OM_S, OBS_OM_W
        filename : string
            file name to be used to store the postcard, optional, default None
        verbose : bool
            optional, default 'False'
            Flag to display information about the process

        Returns
        -------
        None. It downloads the observation postcard indicated
        """

        retri_type = "RETRIEVAL_TYPE=POSTCARD"
        obs_id = "OBSERVATION_ID=" + observation_id
        img_type = "OBS_IMAGE_TYPE=" + image_type
        protocol = "PROTOCOL=HTTP"
        link = self.data_url + "&".join([retri_type, obs_id,
                                         img_type, protocol])

        result = self._handler.request('GET', link, params=None)

        if verbose:
            log.info(link)

        if result is not None:
            result.raise_for_status()

            if filename is None:
                if "Content-Disposition" in result.headers.keys():
                    filename = re.findall('filename="(.+)"',
                                          result.headers[
                                              "Content-Disposition"])[0]
                else:
                    filename = observation_id + ".PNG"

            self._handler.get_file(filename, response=result, verbose=verbose)

            return filename

    def query_xsa_tap(self, query, output_file=None,
                      output_format="votable", verbose=False):
        """Launches a synchronous job to query the XSA tap

        Parameters
        ----------
        query : str, mandatory
            query (adql) to be executed
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            possible values 'votable' or 'csv'
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """

        job = self._tap.launch_job(query=query, output_file=output_file,
                                   output_format=output_format,
                                   verbose=False,
                                   dump_to_file=output_file is not None)
        table = job.get_results()
        return table

    def get_tables(self, only_names=True, verbose=False):
        """Get the available table in XSA TAP service

        Parameters
        ----------
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of tables
        """

        tables = self._tap.load_tables(only_names=only_names,
                                       include_shared_tables=False,
                                       verbose=verbose)
        if only_names is True:
            table_names = []
            for t in tables:
                table_names.append(t.name)
            return table_names
        else:
            return tables

    def get_columns(self, table_name, only_names=True, verbose=False):
        """Get the available columns for a table in XSA TAP service

        Parameters
        ----------
        table_name : string, mandatory, default None
            table name of which, columns will be returned
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of columns
        """

        tables = self._tap.load_tables(only_names=False,
                                       include_shared_tables=False,
                                       verbose=verbose)
        columns = None
        for table in tables:
            if str(table.name) == str(table_name):
                columns = table.columns
                break

        if columns is None:
            raise ValueError("table name specified is not found in "
                             "XSA TAP service")

        if only_names is True:
            column_names = []
            for c in columns:
                column_names.append(c.name)
            return column_names
        else:
            return columns


XMMNewton = XMMNewtonClass()
