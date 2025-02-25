# -*- coding: utf-8 -*-
{
    'name': "Custom Website Sale",
    'version': '18.0.0.1',
    'category': 'Website/Website',
    'description': """ Custom Website Sale """,
    'depends': ['website_sale', 'website'],

    'data': [

        'views/template.xml',

    ],

    'assets': {
        'web.assets_frontend': [
            'custom_website_sale\static\src\js\website_address.js',
            ],
    },

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',

}

