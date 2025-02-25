# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _lt
from odoo.http import request, route
from odoo.addons.website_sale.controllers.main import WebsiteSale


class CustomWebsiteSale(WebsiteSale):

    @route(
        '/shop/address/submit', type='http', methods=['POST'], auth='public', website=True,
        sitemap=False
    )
    def shop_address_submit(
        self, partner_id=None, address_type='billing', use_delivery_as_billing=None, callback=None,
        required_fields=None, **form_data
    ):
        shop_address = super().shop_address_submit(partner_id, address_type,
                                                   use_delivery_as_billing,
                                                   callback, required_fields, **form_data)

        address_values, extra_form_data = self._parse_form_data(form_data)
        order_sudo = request.website.sale_get_order()
        partner_sudo, address_type = self._prepare_address_update(
            order_sudo, partner_id=partner_id and int(partner_id), address_type=address_type
        )
        # partner_id = request.env['res.partner'].sudo().browse(partner_id)
        if partner_sudo and extra_form_data and extra_form_data['city_id']:
            city_id = request.env['res.city'].sudo().browse(int(extra_form_data['city_id']))
            partner_sudo.sudo().write({'city_id': city_id.id, 'street': city_id.name, 'city': city_id.name})

        return shop_address

    def _prepare_address_form_values(self, order_sudo, partner_sudo, address_type, **kwargs):
        rendering_values = super()._prepare_address_form_values(
            order_sudo, partner_sudo, address_type=address_type, **kwargs
        )


        city = partner_sudo.city_id
        state = partner_sudo.state_id
        ResCitySudo = request.env['res.city'].sudo()
        ResCountrySudo = request.env['res.country'].sudo()
        ResCountryStateSudo = request.env['res.country.state'].sudo()
        country_id = request.env['res.country'].sudo().search([('code', '=', 'DZ')])

        rendering_values.update({
            'state': state,

            'state_cities': ResCitySudo.search([('state_id', '=', state.id)]) if state else ResCitySudo,
            'city': city,

            'country': country_id,
            'country_states': ResCountryStateSudo.search([('country_id', '=', country_id.id)]),
            'countries': ResCountrySudo.search([('code', '=', 'DZ')]),

            'zip_before_city': False
        })

        print('state_id--------', rendering_values)
        return rendering_values

    @route(
        '/shop/city_infos/<model("res.country.state"):state>',
        type='json',
        auth='public',
        methods=['POST'],
        website=True,
    )
    def city_infos(self, state, **kw):
        states = request.env['res.city'].sudo().search([('state_id', '=', state.id)])
        print('states--------', states)
        return {'state_cities': [(c.id, c.name) for c in states]}
