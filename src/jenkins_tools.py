#!/usr/bin/env python
# coding: utf-8
# version: 0.1.1

from lxml import html
import click 
import requests

from config_parser import get_section

jenkins_conf = get_section("jenkins")

class JenkinsRoleStrategy(object):
	def __init__(self, url, username, password):

		self.username = username
		self.password = password

		self.url = url
		self.uri_prefix = "/role-strategy/strategy"

		self.roleTypes = {"globalRoles": "globalRoles", 
							"projectRoles": "projectRoles", 
							"slaveRoles": "slaveRoles"}

		self.session = requests.Session()
		self.session.auth = (self.username, self.password)
		self.__get_jenkins_crumb()

		self.uri_role_list   	= 	"/getAllRoles"
		self.uri_role_add 	 	= 	"/addRole"
		self.uri_role_remove 	= 	"/removeRoles"
		self.uri_role_assign 	= 	"/assignRole"
		self.uri_role_unassign 	= 	"/unassignRole"
		self.uri_role_delete_sid= 	"/deleteSid" 		# Delete SID from all roles (specify role types)
	
	def __gen_url(self, uri):
		return self.url + self.uri_prefix + uri
	
	def __get_jenkins_crumb(self):
		crumb_uri = '/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)'
		req = self.session.get(self.url + crumb_uri)
		if req.status_code == 200:
			crumb = req.text.split(":")
			self.session.headers[crumb[0]] = crumb[1]
		print(req, req.text) 	#, req.json()

	def __get_all_roles(self, role_type):
		# {"roleName": ["userlist"]}
		param = dict(type=role_type)
		req = self.session.get(self.__gen_url(self.uri_role_list), params=param)
		return req.json()

	def gen_role_pattern(self, project_env, project_name):
		return "%s.*%s.*" % (project_env, project_name)

	def globalRoles(self):
		role_type = self.roleTypes["globalRoles"]
		return self.__get_all_roles(role_type)

	def projectRoles(self):
		## for Role Strategy Plugin v2.8
		# role_type = self.roleTypes["projectRoles"]
		# return self.__get_all_roles(role_type)

		return self._sort_role()

	def slaveRoles(self):
		## for Role Strategy Plugin v2.8
		# role_type = self.roleTypes["slaveRoles"]
		# return self.__get_all_roles(role_type)

		return
	
	def is_role_type_exist(self, role_type):
		return role_type in self.roleTypes

	def is_role_exist(self, role_name=None, role_type="projectRoles"):
		if self.is_role_type_exist(role_type):
			return role_name in getattr(self, role_type)()

	def add_role(self, role_name, role_type="projectRoles", role_pattern=None, role_overwrite=False):
		
		role_pattern = role_pattern.split("|")

		if not self.is_role_type_exist(role_type):
			return "Role Types %s is not exist!"

		if self.is_role_exist(role_name=role_name, role_type=role_type):
			old_pattern = self._parse_manage_role_page().get(role_name)
			role_pattern = set(role_pattern + old_pattern) if isinstance(old_pattern, list) else old_pattern

			print(role_pattern)
			self.remove_role(role_name=role_name, role_type=role_type)

		data = dict(type=role_type, roleName=role_name, overwrite=True, pattern="|".join(role_pattern))
		
		if role_type == self.roleTypes["projectRoles"]:
			data["permissionIds"] = """com.cloudbees.plugins.credentials.CredentialsProvider.View,hudson.model.Item.Build,hudson.model.Item.Cancel,hudson.model.Item.Read,hudson.model.Item.Workspace"""
		return self.session.post(self.__gen_url(self.uri_role_add), data=data)

	def remove_role(self, role_name, role_type="projectRoles"):
		
		if not self.is_role_exist(role_name=role_name, role_type=role_type):
			return "%s is not exist in %s!" % (role_name, role_type)

		data = dict(type=role_type, roleNames=role_name)
		return self.session.post(self.__gen_url(self.uri_role_remove), data=data)

	def assign_role(self, role_name, user_name, role_type="projectRoles"):

		if not self.is_role_exist(role_name=role_name, role_type=role_type):
			raise ValueError("%s in %s is not exist!" % (role_name, role_type))

		data = dict(type=role_type, roleName=role_name, sid=user_name)
		return self.session.post(self.__gen_url(self.uri_role_assign), data=data)
	
	def unassign_role(self, role_name, user_name, role_type="projectRoles"):
		
		if all([self.is_role_type_exist(role_type), self.is_role_exist(role_name=role_name, role_type=role_type)]):
			if user_name in getattr(self, role_type)().get(role_name):
				data = dict(type=role_type, roleName=role_name, sid=user_name)
				return self.session.post(self.__gen_url(self.uri_role_unassign), data=data)

		return "%s:%s is not exist!" % (role_type, role_name)

	def delete_sid_from_all_roles(self, user_name, role_type="all"):
		
		if role_type == "all":
			role_type = self.roleTypes.values()
		else:
			role_type = [role_type]
		
		for rt in role_type:
			data = dict(type=rt, sid=user_name)
			self.session.post(self.__gen_url(self.uri_role_delete_sid), data=data)

	def _clean_fkh(self, val):
		if isinstance(val, str):
			return val.replace("[", "").replace("]", '')
		return val

	def _parse_assign_role_page(self):
		url = self.url + "/role-strategy/assign-roles" 
		req = self.session.get(url)
		d = {}
		if req.status_code == 200:
			tree = html.fromstring(req.text)
			pr_html = tree.xpath("//table[@id='projectRoles']")[0]
			for tr in pr_html.xpath(".//tr"):
				if tr.get("name"):
					ipts = tr.xpath(".//td[@width='*']/input")

					d[self._clean_fkh(tr.get("name"))] = {self._clean_fkh(ipt.get("name")): self._clean_fkh(ipt.get("checked")) for ipt in ipts}
					d[self._clean_fkh(tr.get("name"))] = {self._clean_fkh(ipt.get("name")): self._clean_fkh(ipt.get("checked")) for ipt in ipts}					
			return d

		raise requests.ConnectionError(url)

	def _parse_manage_role_page(self):
		# "{ROLE_NAME: ROLE_PATTERN_LIST}"
		url = self.url + "/role-strategy/manage-roles"
		req = self.session.get(url)
		d = {}
		if req.status_code == 200:
			tree = html.fromstring(req.text)
			pr_html = tree.xpath("//table[@id='projectRoles']")[0]
			for tr in pr_html.xpath(".//tr"):
				if tr.get("name"):
					pattern = tr.xpath(".//td[@class='in-place-edit']/text()")[0]
					d[self._clean_fkh(tr.get("name"))] = pattern.strip().split("|")
			return d
		raise requests.ConnectionError(url)

	def _sort_role(self):
		data = self._parse_assign_role_page()
		nd = {}
		if data:
			for user, role_matrix in data.items():
				for role_name, role_chk in role_matrix.items():
					if not nd.get(role_name):
						nd[role_name] = []
					if role_chk:
						nd[role_name].append(user)
		
		return nd


def jks_role_auth(admin_name, admin_pass):
    return JenkinsRoleStrategy(jenkins_conf.get("jenkins_url"), admin_name, admin_pass)


@click.group()
@click.option('--admin-name', "-U", default=jenkins_conf.get("admin_name"), help='You Useranme to Login Jenkins Server.')
@click.option('--admin-pass', "-P", default=jenkins_conf.get("admin_pass"), help='You Password to Login Jenkins Server.')
@click.pass_context
def cli(ctx, admin_name, admin_pass):
    if not all([admin_name, admin_pass]):
        raise ValueError("Admin Name %s and Admin Password %s cann't empty!" % (admin_name, admin_pass))
    ctx.obj = {
        "admin_name": admin_name, 
        "admin_pass": admin_pass,
    }

@click.command()
@click.option("--role-name", help="Role to be Added")
@click.option("--role-type", default="projectRoles", type=click.Choice(["projectRoles", "globalRoles"]), help="Role Types, default is projectRoles")
@click.option("--role-pattern", help="Role Pattern, default is Project Ci Name")
@click.option("--role-overwrite", default=False, help="If Role is Exist, Overwrite it or not, defaut is False.")
@click.pass_context
def add_role(ctx, role_name, role_type, role_pattern, role_overwrite):
    jks = jks_role_auth(ctx.obj["admin_name"], ctx.obj["admin_pass"])
    jks.add_role(role_name=role_name, role_type=role_type, role_pattern=role_pattern, role_overwrite=role_overwrite)

@click.command()
@click.option("--role-name", help="Role to be Remove")
@click.option("--role-type", default="projectRoles", type=click.Choice(["projectRoles", "globalRoles"]), help="Role Types, default is projectRoles")
@click.pass_context
def remove_role(ctx, role_name, role_type):
    jks = jks_role_auth(ctx.obj["admin_name"], ctx.obj["admin_pass"])
    jks.remove_role(role_name=role_name, role_type=role_type)
    
@click.command()
@click.option("--role-name", help="Role to be Assign")
@click.option("--user-name", help="Username to be assigned to Role")
@click.option("--role-type", default="projectRoles", type=click.Choice(["projectRoles", "globalRoles"]), help="Role Types, default is projectRoles")
@click.pass_context
def assign_role(ctx, role_name, user_name, role_type):
    jks = jks_role_auth(ctx.obj["admin_name"], ctx.obj["admin_pass"])
    jks.assign_role(role_name=role_name, user_name=user_name, role_type=role_type)

@click.command()
@click.option("--role-name", help="Role to be Unassigned")
@click.option("--user-name", help="Username to be Unassigned to Role")
@click.option("--role-type", default="projectRoles", type=click.Choice(["projectRoles", "globalRoles"]), help="Role Types, default is projectRoles")
@click.pass_context
def unassign_role(ctx, role_name, user_name, role_type):
    jks = jks_role_auth(ctx.obj["admin_name"], ctx.obj["admin_pass"])
    jks.unassign_role(role_name, user_name, role_type="projectRoles")

@click.command()
@click.option("--user-name", help="Username to be Unassigned to Role")
@click.option("--role-type", default="all", type=click.Choice(["all", "projectRoles", "globalRoles"]), help="Role Types, default is all")
@click.pass_context
def delete_user(ctx, user_name, role_type):
    jks = jks_role_auth(ctx.obj["admin_name"], ctx.obj["admin_pass"])
    jks.delete_sid_from_all_roles(user_name=user_name, role_type=role_type)

cli.add_command(add_role, "add-role")
cli.add_command(remove_role, "remove-role")
cli.add_command(assign_role, "assign-role")
cli.add_command(unassign_role, "unassign-role")
cli.add_command(delete_user, "delete-user")


if __name__ == "__main__":
    cli()
