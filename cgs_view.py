#!/usr/local/bin/python
# -*- coding: UTF-8

from . import cgs_api

@cgs_api.route('/cgs', methods=['GET'])
def index():   
    return 'This is for CGS applications.'
