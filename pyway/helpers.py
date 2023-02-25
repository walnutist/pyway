import os
import re
import zlib

from . import settings
from .log import logger
from .errors import VALID_NAME_ERROR, DIRECTORY_NOT_FOUND, MIGRATIONS_NOT_FOUND, OUT_OF_DATE_ERROR


class Utils():

    @staticmethod
    def subtract(list_a, list_b):
        # Subtract list_b from list_a
        result = []
        if list_a and list_b:
            checksum_list_b = [b.checksum for b in list_b]
            result = [a for a in list_a if a.checksum not in checksum_list_b]
        elif list_a and not list_b:
            # List B is empty (usually from a new install)
            return list_a
        return result

    @staticmethod
    def expected_pattern():
        return "%s{major}_{minor}%s{description}%s" % \
            (settings.SQL_MIGRATION_PREFIX, settings.SQL_MIGRATION_SEPARATOR, settings.SQL_MIGRATION_SUFFIXES)

    @staticmethod
    def is_file_name_valid(name):
        _pattern = r"^%s\d+_\d{2}%s\w+%s$" % \
            (settings.SQL_MIGRATION_PREFIX, settings.SQL_MIGRATION_SEPARATOR, settings.SQL_MIGRATION_SUFFIXES)
        return re.match(_pattern, name, re.IGNORECASE) is not None

    @staticmethod
    def sort_migrations_list(migrations):
        return sorted(migrations, key=lambda x: [x.get("version"), x.get("name")] if isinstance(x, dict) else
                                                [x.version, x.name], reverse=False)


    @staticmethod
    def flatten_migrations(migrations):
        migration_list = []
        for m in migrations:
            migration_list.append({ 'version': m.version, 'extension': m.extension, 'name': m.name, 'checksum': m.checksum, 'apply_timestamp': m.apply_timestamp })
        return migration_list


    @staticmethod
    def get_version_from_name(name):
        try:
            return re.findall(r"\d+_\d{2}", name)[0].replace('_', '.')
        except IndexError:
            logger.error(VALID_NAME_ERROR % (name, Utils.expected_pattern()))

    @staticmethod
    def get_extension_from_name(name):
        return name.split('.')[1].upper()

    @staticmethod
    def load_checksum_from_name(name):
        fullname = Utils.fullname(name)
        prev = 0
        try:
            for line in open(fullname, "rb"):
                prev = zlib.crc32(line, prev)
            return "%X" % (prev & 0xFFFFFFFF)
        except FileNotFoundError:
            logger.error(OUT_OF_DATE_ERROR % fullname.split("/")[-1])

    @staticmethod
    def fullname(name):
        return os.path.join(Utils.basepath(), name)

    @staticmethod
    def basepath():
        return os.path.join(os.getcwd(), settings.DATABASE_MIGRATION_DIR)

    @staticmethod
    def get_min_version_from_local_migrations():
        return min([int(Utils.get_version_from_name(file.name)) for file in os.listdir(Utils.basepath())])

    @staticmethod
    def get_local_files():
        path = Utils.basepath()
        dir_list = None
        try:
            dir_list = os.listdir(path)
        except OSError:
            logger.error(DIRECTORY_NOT_FOUND % path)
        return dir_list

    @staticmethod
    def create_map_from_list(key, list_):
        return {l.__dict__[key]: l for l in list_}
