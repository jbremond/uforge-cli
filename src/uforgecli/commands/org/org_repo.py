__author__ = "UShareSoft"

from texttable import Texttable
from ussclicore.argumentParser import ArgumentParser, ArgumentParserError
from uforgecli.utils.uforgecli_utils import *
from ussclicore.cmd import Cmd, CoreGlobal
from uforgecli.utils import org_utils
from ussclicore.utils.generics_utils import order_list_object_by
from ussclicore.utils import printer
from org_repo_os import Org_Repo_Os_Cmd
from uforge.objects import uforge
from ussclicore.utils import generics_utils
from uforgecli.utils import uforgecli_utils
import pyxb
import datetime
import shlex

class Org_Repo_Cmd(Cmd, CoreGlobal):
        """Repository operation (list|create|delete|update)"""

        cmd_name = "repo"

        def __init__(self):
                self.generate_sub_commands()
                super(Org_Repo_Cmd, self).__init__()

        def generate_sub_commands(self):
                if not hasattr(self, 'subCmds'):
                        self.subCmds = {}

                orgRepoOs = Org_Repo_Os_Cmd()
                self.subCmds[orgRepoOs.cmd_name] = orgRepoOs

        def arg_list(self):
                doParser = ArgumentParser(add_help = True, description="List all the repositories for the provided organization")

                optional = doParser.add_argument_group("optional arguments")

                optional.add_argument('--org', dest='org', type=str, required=False, help="The organization name. If no organization is provided, then the default organization is used.")
                optional.add_argument('--sortField', dest='sort', type=str, required=False, help="Sort the repository list by a field between Name, ID, Url and Type")

                return doParser

        def do_list(self, args):
                try:
                        doParser = self.arg_list()
                        doArgs = doParser.parse_args(shlex.split(args))

                        org = org_utils.org_get(self.api, doArgs.org)
                        allRepo = self.api.Orgs(org.dbId).Repositories.Getall()

                        if allRepo is None:
                                printer.out("No repositories found in [" + org.name + "].")
                                return 0

                        if doArgs.sort is not None:
                                if doArgs.sort.lower() == "name":
                                        printer.out("Repository list ordered by [name] :")
                                        allRepo = order_list_object_by(allRepo.repositories.repository, "name")
                                elif doArgs.sort.lower() == "id":
                                        printer.out("Repository list ordered by [id] :")
                                        allRepo = sorted(allRepo.repositories.repository, key=lambda x: getattr(x, "dbId"), reverse=False)
                                elif doArgs.sort.lower() == "url":
                                        printer.out("Repository list ordered by [url] :")
                                        allRepo = order_list_object_by(allRepo.repositories.repository, "url")
                                elif doArgs.sort.lower() == "type":
                                        printer.out("Repository list ordered by [type] :")
                                        allRepo = order_list_object_by(allRepo.repositories.repository, "packagingType")
                                else:
                                        printer.out("Sorting parameter filled don't exist.", printer.WARNING)
                                        printer.out("Repository list :")
                                        allRepo = sorted(allRepo.repositories.repository, key=lambda x: getattr(x, "dbId"), reverse=False)
                        else:
                                printer.out("Repository list :")
                                allRepo = sorted(allRepo.repositories.repository, key=lambda x: getattr(x, "dbId"), reverse=False)

                        table = Texttable(200)
                        table.set_cols_align(["c", "c", "l", "l", "c"])
                        table.set_cols_width([5,5,30,80,8])
                        table.header(["Id", "Off. Supported", "Name", "URL", "Type"])

                        for item in allRepo:
                                if item.officiallySupported:
                                        officiallySupported = "X"
                                else:
                                        officiallySupported = ""
                                table.add_row([item.dbId, officiallySupported, item.name, item.url, item.packagingType])

                        print table.draw() + "\n"

                        printer.out("Found " + str(len(allRepo)) + " repositories.")

                        return 0

                except ArgumentParserError as e:
                        printer.out("In Arguments: "+str(e), printer.ERROR)
                        self.help_list()
                except Exception as e:
                        return handle_uforge_exception(e)

        def help_list(self):
                doParser = self.arg_list()
                doParser.print_help()

        def arg_create(self):
                doParser = ArgumentParser(add_help = True, description="Create a repository in the organization")

                mandatory = doParser.add_argument_group("mandatory arguments")
                optional = doParser.add_argument_group("optional arguments")

                mandatory.add_argument('--name', dest='name', type=str, required=True, help="Repository name.")
                mandatory.add_argument('--repoUrl', dest='repoUrl', type=str, required=True, help="Url of the repository to create in the organization.")
                mandatory.add_argument('--type', dest='type', type=str, required=True, help="Type of the repository to create in the organization ('RPM' or 'DEB').")
                optional.add_argument('--org', dest='org', type=str, required=False, help="The organization name. If no organization is provided, then the default organization is used.")
                optional.add_argument('--officiallySupported', dest='officiallySupported', action="store_true", required=False, help="The organization name. If no organization is provided, then the default organization is used.")

                return doParser

        def do_create(self, args):
                try:
                        doParser = self.arg_create()
                        doArgs = doParser.parse_args(shlex.split(args))

                        org = org_utils.org_get(self.api, doArgs.org)
                        allRepo = self.api.Orgs(org.dbId).Repositories.Getall()
                        allRepo = allRepo.repositories.repository

                        for item in allRepo:
                                if doArgs.repoUrl == item.url:
                                        printer.out("The repository with URL [" + item.url + "] already exist in [" + org.name + "].", printer.ERROR)
                                        return 0

                        newRepository = repository()
                        newRepository.url = doArgs.repoUrl
                        newRepository.packagingType = doArgs.type
                        newRepository.name = doArgs.name
                        newRepository.officiallySupported = doArgs.officiallySupported

                        result = self.api.Orgs(org.dbId).Repositories.Create(body=newRepository)
                        printer.out("Successfully created repository with URL [" + doArgs.repoUrl + "] in [" + org.name + "].", printer.OK)
                        return 0

                except ArgumentParserError as e:
                        printer.out("In Arguments: "+str(e), printer.ERROR)
                        self.help_create()
                except Exception as e:
                        return handle_uforge_exception(e)

        def help_create(self):
                doParser = self.arg_create()
                doParser.print_help()

        def arg_delete(self):
                doParser = ArgumentParser(add_help = True, description="Delete a repository in the organization")

                mandatory = doParser.add_argument_group("mandatory arguments")
                optional = doParser.add_argument_group("optional arguments")

                mandatory.add_argument('--ids', dest='ids', nargs='+', required=True, help="One or more repositories to delete (repository Ids provided) in the organization.  Ids separated by space (e.g. 1 2 3)")
                optional.add_argument('--org', dest='org', type=str, required=False, help="The organization name. If no organization is provided, then the default organization is used.")

                return doParser

        def do_delete(self, args):
                try:
                        doParser = self.arg_delete()
                        doArgs = doParser.parse_args(shlex.split(args))

                        org = org_utils.org_get(self.api, doArgs.org)

                        for item in doArgs.ids:
                                result = self.api.Orgs(org.dbId).Repositories(item).Delete()
                                printer.out("Repository with ID [" + str(item) + "] deleted.", printer.OK)

                        return 0

                except ArgumentParserError as e:
                        printer.out("In Arguments: "+str(e), printer.ERROR)
                        self.help_delete()
                except Exception as e:
                        return handle_uforge_exception(e)

        def help_delete(self):
                doParser = self.arg_delete()
                doParser.print_help()

        def arg_update(self):
                doParser = ArgumentParser(add_help = True, description="Update a repository in the organization")

                mandatory = doParser.add_argument_group("mandatory arguments")
                optional = doParser.add_argument_group("optional arguments")

                mandatory.add_argument('--id', dest='id', type=int, required=True, help="Id of the repository to update in the organization.")
                optional.add_argument('--repoUrl', dest='repoUrl', type=str, required=False, help="Url of the repository to update in the organization.")
                optional.add_argument('--type', dest='type', type=str, required=False, help="Type of the repository to update in the organization.")
                optional.add_argument('--org', dest='org', type=str, required=False, help="The organization name. If no organization is provided, then the default organization is used.")

                return doParser

        def do_update(self, args):
                try:
                        doParser = self.arg_update()
                        doArgs = doParser.parse_args(shlex.split(args))

                        org = org_utils.org_get(self.api, doArgs.org)
                        allRepo = self.api.Orgs(org.dbId).Repositories.Getall()
                        allRepo = allRepo.repositories.repository

                        if doArgs.repoUrl is None and doArgs.type is None:
                                printer.out("No change has been specified.")
                                return 0

                        for item in allRepo:
                                if doArgs.repoUrl == item.url:
                                        printer.out("The URL is already used by repository with ID [" + str(item.dbId) + "]", printer.ERROR)
                                        return 0
                                if doArgs.id == item.dbId:
                                        newRepository = repository()
                                        newRepository.url = item.url
                                        newRepository.packagingType = item.packagingType
                                        newRepository.name = item.name
                                        newRepository.officiallySupported = item.officiallySupported
                                        if doArgs.repoUrl is not None:
                                                newRepository.url = doArgs.repoUrl
                                        if doArgs.type is not None:
                                                newRepository.packagingType = doArgs.type
                                        result = self.api.Orgs(org.dbId).Repositories(item.dbId).Update(body=newRepository)
                                        printer.out("Updated repository with ID [" + str(doArgs.id) + "].", printer.OK)
                                        return 0

                        printer.out("The repository specified doesn't exist.", printer.ERROR)
                        return 0

                except ArgumentParserError as e:
                        printer.out("In Arguments: "+str(e), printer.ERROR)
                        self.help_update()
                except Exception as e:
                        return handle_uforge_exception(e)

        def help_update(self):
                doParser = self.arg_update()
                doParser.print_help()
