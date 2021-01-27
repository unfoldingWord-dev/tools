import os
import tempfile
import json
import time
import traceback
from glob import glob
from shutil import copyfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union

from rq_settings import prefix, debug_mode_flag
from app_settings.app_settings import AppSettings
from general_tools import file_utils
from general_tools.file_utils import write_file, remove_tree
from door43_tools.templaters import init_template, get_sorted_Bible_html_filepath_list



class ProjectDeployer:
    """
    Deploys a project's revision to the door43.org bucket

    Read from the project's user dir in the cdn.door43.org bucket
    by applying the door43.org template to the raw html files
    """

    def __init__(self, unzip_dir:str, temp_dir:str) -> None:
        AppSettings.logger.debug(f"ProjectDeployer.__init__({unzip_dir}, {temp_dir})…")
        self.unzip_dir = unzip_dir
        self.temp_dir = tempfile.mkdtemp(prefix='deployer_', dir=temp_dir)
        self.error_messages:List[str] = []


    def close(self) -> None:
        pass


    def deploy_revision_to_door43(self, build_log:Dict[str,Any]) -> bool:
        """
        Deploys a single revision of a project to door43.org

        Templates the converted files
            then uploads them and the build log to the S3 bucket
            and creates a 'deployed' file there too.

        :param dict build_log:
        :return bool:
        """
        start = time.time()
        AppSettings.logger.debug(f"Deploying, build log: {json.dumps(build_log)[:256]} …")
        assert 'multiple' not in build_log
        assert 'part' not in build_log

        user = build_log['repo_owner_username'] # was 'repo_owner'
        repo_name = build_log['repo_name']
        commit_id = build_log['commit_id'] # Hashes should already be reduced to 10 characters

        s3_commit_key = f'u/{user}/{repo_name}/{commit_id}'
        s3_repo_key = f'u/{user}/{repo_name}'

        source_dir = tempfile.mkdtemp(prefix='source_', dir=self.temp_dir)
        template_dir = tempfile.mkdtemp(prefix='template_', dir=self.temp_dir)
        output_dir = tempfile.mkdtemp(prefix='output_', dir=self.temp_dir)


        # Do the templating first
        resource_type = build_log['resource_type']
        template_key = 'templates/project-page.html'
        template_file = os.path.join(template_dir, 'project-page.html')
        AppSettings.logger.info(f"Downloading project page template from {AppSettings.door43_bucket_name} '{template_key}' to {template_file} …")
        AppSettings.door43_s3_handler().download_file(template_key, template_file)
        source_dir, success = self.template_converted_files(build_log, output_dir, repo_name,
                                            resource_type, s3_commit_key, source_dir, start,
                                            template_file)
        build_log['warnings'].extend(self.error_messages)
        if not success:
            AppSettings.logger.critical("Templating failed—returning False")
            return False


        #######################
        #
        #  Now do the deploy
        #
        #######################

        # Copy first HTML file to index.html if index.html doesn't exist
        # html_files = get_sorted_Bible_html_filepath_list(output_dir) if 'Bible' in resource_type \
        #                 else sorted(glob(os.path.join(output_dir, '*.html')))
        html_files = get_sorted_Bible_html_filepath_list(output_dir)
        index_file = os.path.join(output_dir, 'index.html')
        if html_files and not os.path.isfile(index_file):
            copyfile(os.path.join(output_dir, html_files[0]), index_file)

        # Copy all other files over that don't already exist in output_dir, like css files
        #   Copying from source_dir to output_dir (both are folders inside main temp folder)
        for filename in sorted(glob(os.path.join(source_dir, '*'))):
            output_file = os.path.join(output_dir, os.path.basename(filename))
            if not os.path.exists(output_file) and not os.path.isdir(filename):
                copyfile(filename, output_file)

        # Save master build_log.json
        build_log['ended_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        file_utils.write_file(os.path.join(output_dir, 'build_log.json'), build_log)
        AppSettings.logger.debug(f"Final build_log.json: {json.dumps(build_log)[:256]} …")

        # Upload all files to the S3 door43.org bucket
        AppSettings.logger.info(f"Uploading all files to the website bucket: {AppSettings.door43_bucket_name} …")
        for root, _dirs, files in os.walk(output_dir):
            for filename in sorted(files):
                filepath = os.path.join(root, filename)
                if os.path.isdir(filepath):
                    continue
                key = s3_commit_key + filepath.replace(output_dir, '').replace(os.path.sep, '/')
                AppSettings.logger.debug(f"Uploading {filename} to {AppSettings.door43_bucket_name} bucket {key} …")
                AppSettings.door43_s3_handler().upload_file(filepath, key, cache_time=0)

        # Now we place json files and redirect index.html for the whole repo to this index.html file
        AppSettings.logger.info("Copying json files and setting up redirect…")
        try:
            AppSettings.door43_s3_handler().copy(from_key=f'{s3_repo_key}/project.json', from_bucket=AppSettings.cdn_bucket_name)
            AppSettings.door43_s3_handler().copy(from_key=f'{s3_commit_key}/manifest.json',
                                                    to_key=f'{s3_repo_key}/manifest.json')
            AppSettings.door43_s3_handler().redirect(key=s3_repo_key, location='/' + s3_commit_key)
            AppSettings.door43_s3_handler().redirect(key=s3_repo_key + '/index.html',
                                                        location='/' + s3_commit_key)
            self.write_data_to_file_and_upload_to_CDN(output_dir, s3_commit_key, fname='deployed', data=' ')  # flag that deploy has finished
        except Exception as e:
            AppSettings.logger.critical(f"Deployer threw an exception: {e}: {traceback.format_exc()}")

        elapsed_seconds = int(time.time() - start)
        AppSettings.logger.debug(f"Deploy completed in {elapsed_seconds} seconds.")
        self.close()
        return True
    # end of ProjectDeployer.deploy_revision_to_door43(build_log)


    def template_converted_files(self, build_log:Dict[str,Any], output_dir:str,
                                    repo_name:str, resource_type:str, s3_commit_key:str,
                                    source_dir:str, start_time, template_filepath:str):
        AppSettings.logger.debug(f"template_converted_files((build_log), od={output_dir}, '{repo_name}'," \
                                   f" '{resource_type}', k={s3_commit_key}, sd={source_dir}," \
                                   f" {start_time}, tf={template_filepath}) with {self.unzip_dir}…")
        assert 'errors' in build_log
        assert 'message' in build_log
        assert repo_name
        source_dir = self.unzip_dir
        html_files = sorted(glob(os.path.join(source_dir, '*.html')))
        if len(html_files) < 1:
            AppSettings.logger.warning("No html files found by ProjectDeployer.template_converted_files!")
            content = ""
            if build_log['errors']:
                content += """
                        <div style="text-align:center;margin-bottom:20px">
                            <em class="fa fa-times-circle-o" style="font-size: 250px;font-weight: 300;color: red"></em>
                            <br/>
                            <h2>Critical!</h2>
                            <h3>Here is what went wrong with this build:</h3>
                        </div>
                    """
                content += '<div><ul><li>' + '</li><li>'.join(build_log['errors']) + '</li></ul></div>'
            else:
                content += f'<h1 class="conversion-requested">{build_log["message"]}</h1>'
                content += f'<p><em>No content is available to show for {repo_name} yet.</em></p>'
            html = f"""
                    <html lang="en">
                        <head>
                            <title>{repo_name}</title>
                        </head>
                        <body>
                            <div id="content">{content}</div>
                        </body>
                    </html>"""
            repo_index_file = os.path.join(source_dir, 'index.html')
            write_file(repo_index_file, html)

        # Merge the source files with the template
        templater = init_template(resource_type, source_dir, output_dir, template_filepath)
        try:
            self.run_templater(templater)
            success = True
        except Exception as e:
            AppSettings.logger.error(f"Error applying template {template_filepath} to resource type {resource_type}:")
            AppSettings.logger.error(f'{e}: {traceback.format_exc()}')
            self.close()
            success = False

        if success:
            # Update index of templated files
            index_json_fname = 'index.json'
            index_json = self.get_templater_index(s3_commit_key, index_json_fname)
            # AppSettings.logger.debug(f"Initial 'index.json': {json.dumps(index_json)[:256]}")
            # AppSettings.logger.debug(f"Initial 'index.json': {index_json}")
            # AppSettings.logger.debug(f"Templater titles: {getattr(templater, 'titles')}")
            self.update_index_key(index_json, templater, 'titles')
            # AppSettings.logger.debug(f"Templater chapters: {getattr(templater, 'chapters')}")
            self.update_index_key(index_json, templater, 'chapters')
            # AppSettings.logger.debug(f"Templater book_codes: {getattr(templater, 'book_codes')}")
            self.update_index_key(index_json, templater, 'book_codes')
            # AppSettings.logger.debug(f"Final 'index.json': {json.dumps(index_json)[:256]} …")
            # AppSettings.logger.debug(f"Final 'index.json': {index_json}")
            self.write_data_to_file_and_upload_to_CDN(output_dir, s3_commit_key,
                                                        index_json_fname, index_json)
        return source_dir, success
    # end of ProjectDeployer.template_converted_files function


    def write_data_to_file_and_upload_to_CDN(self, output_dir:str, s3_commit_key:str,
                                                    fname:str, data:Union[str, Dict[str,Any]]) -> None:
        out_file = os.path.join(output_dir, fname)
        write_file(out_file, data)
        key = s3_commit_key + '/' + fname
        AppSettings.logger.debug(f"Uploading '{fname}' to {AppSettings.cdn_bucket_name} {key} …")
        AppSettings.cdn_s3_handler().upload_file(out_file, key, cache_time=0)
    # end of ProjectDeployer.write_data_to_file_and_upload_to_CDN function


    def run_templater(self, templater) -> None:  # for test purposes
        templater.run()
        self.error_messages = list(templater.error_messages)
    # end of ProjectDeployer.run_templater(templater)


    @staticmethod
    def update_index_key(index_json_dict:Dict[str,Any], templater_object, key_string:str) -> None:
        """
        key_string is one of 'titles', chapters', 'book_codes'

        Adds entries to the index_json_dict
        """
        # AppSettings.logger.debug(f"ProjectDeployer.update_index_key({index_json_dict}, , '{key_string}')")
        data = index_json_dict[key_string]
        data.update(getattr(templater_object, key_string))
        index_json_dict[key_string] = data
        # AppSettings.logger.debug(f"ProjectDeployer.update_index_key now has {index_json_dict}")
    # end of ProjectDeployer.update_index_key function


    @staticmethod
    def get_templater_index(s3_commit_key:str, index_json_fname:str) -> Dict[str,Any]:
        index_json = AppSettings.cdn_s3_handler().get_json(s3_commit_key + '/' + index_json_fname)
        if not index_json:
            index_json['titles'] = {}
            index_json['chapters'] = {}
            index_json['book_codes'] = {}
        return index_json
    # end of ProjectDeployer.get_templater_index function
# end of ProjectDeployer class
