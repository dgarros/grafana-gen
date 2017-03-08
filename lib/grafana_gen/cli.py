
import argparse
from jinja2 import Template
import pprint
import yaml
import logging
from os import path
import os
import re
import json
import sys

############################################
### CLI Params
#############################################
def main():


    parser = argparse.ArgumentParser(description='Process user input')
    parser.add_argument("--file",
                        dest="dashboard",
                        help="Definition file for the dashboard to create")

    parser.add_argument("--upload",
                        dest="upload",
                        action="store_true",
                        help="Upload Dashboard to a Grafana server")

    parser.add_argument("--log",
                        dest="log",
                        metavar="LEVEL",
                        default='info',
                        choices=['info', 'warn', 'debug', 'error'],
                        help="Specify the log level ")

    args = parser.parse_args()

    # Print help if no parameters are provided
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    here = path.abspath(path.dirname(__file__))

    pp = pprint.PrettyPrinter(indent=4)

    ############################################
    ### Log level configuration
    #############################################
    logger = logging.getLogger( 'grafana-gen' )

    if args.log == 'debug':
        logger.setLevel(logging.DEBUG)
    elif args.log == 'warn':
        logger.setLevel(logging.WARN)
    elif args.log == 'error':
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)

    logging.basicConfig(format=' %(name)s - %(levelname)s - %(message)s')

    ############################################
    ### Load main configuration file
    #############################################

    TEMPLATES_DIR = os.getcwd() + '/templates/'
    ROWS_DIR = TEMPLATES_DIR +'rows/'
    GRAPHS_DIR = TEMPLATES_DIR + 'graphs/'
    TEMPLATINGS_DIR = TEMPLATES_DIR + 'templatings/'
    ANNOTATIONS_DIR = TEMPLATES_DIR + 'annotations/'

    logger.info('Opening Configuration file {}'.format(args.dashboard))

    # TODO Check if file exist first
    dashboard = yaml.load(open(args.dashboard))

    ############################################
    ### Process ROWS
    #############################################

    if 'rows' in dashboard.keys():
        dashboard['rows_data'] = ''
        nbr_rows = 0
        panel_id = 1

        for row in dashboard['rows']:
            logger.info('Add Row: {}'.format(row))
            row_conf = yaml.load(open(ROWS_DIR + row).read())

            row_conf['panels_data'] = ''
            nbr_panels = 0

            if row_conf['panels']['graphs']:
                ## Find panels for this row
                for graph in row_conf['panels']['graphs']:
                    logger.info('  Add Graph: {}'.format(graph))
                    graph_conf = yaml.load(open(GRAPHS_DIR + graph).read())

                    ## Insert Graph ID and increment
                    graph_conf['id'] = panel_id
                    panel_id = panel_id + 1

                    logger.debug('  Found Template for graph: {}'.format(GRAPHS_DIR + graph_conf['template']))
                    graph_tpl = open(GRAPHS_DIR + graph_conf['template'])

                    ## Find template for this grah and render
                    graph_tpl_rdr = Template(graph_tpl.read()).render(graph_conf)

                    ## Add template to list of panels
                    if nbr_panels > 0:
                        logger.debug('  Not the first panel add a ","')
                        row_conf['panels_data'] = row_conf['panels_data'] + ','
                    row_conf['panels_data'] = row_conf['panels_data'] + graph_tpl_rdr
                    nbr_panels =+ 1

                    ## Check if template is using some templatings and add to the list
                    for templating in graph_conf['templatings_used']:
                        if 'templatings' not in dashboard.keys():
                            dashboard['templatings'] = []
                        dashboard['templatings'].append(templating)
                        logger.debug('  Added templating {} as a requirement'.format(templating))

            ## Render Row and Add it to the dashboard`
            row_tpl = open(ROWS_DIR + row_conf['template'])
            row_tpl_rdr = Template(row_tpl.read()).render(row_conf)

            if nbr_rows > 0:
                logger.debug('Not the first row add a ","')
                dashboard['rows_data'] = dashboard['rows_data'] + ','
            dashboard['rows_data'] = dashboard['rows_data'] + row_tpl_rdr
            nbr_rows =+ 1

    #############################################
    ### Process ANNOTATIONS
    #############################################
    if 'annotations' in dashboard.keys():
        logger.info('Nothing here yet')

        dashboard['annotations_data'] = ''
        nbr_annotations = 0

        ## Extract unique values
        list_annotations = set(dashboard['annotations'])

        for annotation in list(list_annotations):
            logger.info('Add Annotation: {}'.format(annotation))
            annotation_conf = yaml.load(open(ANNOTATIONS_DIR + annotation).read())

            annotation_tpl = open(ANNOTATIONS_DIR + annotation_conf['template'])
            annotation_tpl_rdr = Template(annotation_tpl.read()).render(annotation_conf)

            ## Add template to list of panels
            if nbr_annotations > 0:
                logger.debug('Not the first annotation, add a ","')
                dashboard['annotations_data'] = dashboard['annotations_data'] + ','
            dashboard['annotations_data'] = dashboard['annotations_data'] + annotation_tpl_rdr
            nbr_annotations =+ 1

    #############################################
    ### Process TAGS
    #############################################
    if 'tags' in dashboard.keys():
        tags = '","'.join(map(str, dashboard['tags']))
        dashboard['tags_data'] = '"' + tags + '"'
        logger.info('Add Tag(s): {}'.format(dashboard['tags_data']))

    #############################################
    ### Process TEMPLATINGS
    #############################################
    if 'templatings' in dashboard.keys():
        dashboard['templatings_data'] = ''
        nbr_templatings = 0

        ## Extract unique values
        list_templatings = set(dashboard['templatings'])

        for templating in list(list_templatings):
            logger.info('Add Templating: {}'.format(templating))
            templating_conf = yaml.load(open(TEMPLATINGS_DIR + templating).read())

            templating_tpl = open(TEMPLATINGS_DIR + templating_conf['template'])
            templating_tpl_rdr = Template(templating_tpl.read()).render(templating_conf)

            ## Add template to list of panels
            if nbr_templatings > 0:
                logger.debug('Not the first templating, add a ","')
                dashboard['templatings_data'] = dashboard['templatings_data'] + ','
            dashboard['templatings_data'] = dashboard['templatings_data'] + templating_tpl_rdr
            nbr_templatings =+ 1

    #############################################
    ### Render Dashboard
    #############################################
    dashboard_tpl = open(TEMPLATES_DIR + dashboard['template'])
    dashboard_tpl_rdr = Template(dashboard_tpl.read().decode("utf8")).render(dashboard)

    dashboard_file_name = dashboard['title'].lower() + '.json'
    dashboard_file_name = re.sub(r'\s', '_', dashboard_file_name)

    logger.info('Dashboard File name: {}'.format(dashboard_file_name))

    # Validate JSON and write content to file
    # If content is not valid, write current status in a debug File

    try:
        ## Validate Json
        dashboard_json = json.loads(dashboard_tpl_rdr)

        tmp_json = dict(dashboard=dashboard_json)

        with open(dashboard_file_name, "w") as text_file:
            json.dump(tmp_json, text_file, indent=2)

    except:
        debug_file_name = "debug_" + dashboard_file_name

        logger.warn('JSON not Valid, Debug File: {}'.format(debug_file_name))
        with open(debug_file_name, "w") as text_file:
            text_file.write(dashboard_tpl_rdr)

    if args.upload:
        print "Will upload the dashboard to Grafana"


if __name__ == '__main__':
    main()
