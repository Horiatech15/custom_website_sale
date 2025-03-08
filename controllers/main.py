# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _lt
from odoo.http import request, route
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers import portal as payment_portal


class WebsiteSalePayment(payment_portal.PaymentPortal):

    def _get_mandatory_address_fields(self, country_sudo):
        """ Return the set of common mandatory address fields.

        :param res.country country_sudo: The country to use to build the set of mandatory fields.
        :return: The set of common mandatory address field names.
        :rtype: set
        """

        if country_sudo.code == 'DZ':
            field_names = {'name', 'city', 'country_id', 'state_id'}
        else:
            field_names = super()._get_mandatory_address_fields(country_sudo)

        return field_names


    def _get_mandatory_delivery_address_fields(self, country_sudo):
        mandatory_fields = super()._get_mandatory_delivery_address_fields(country_sudo)
        if country_sudo.code == 'DZ':
            mandatory_fields |= {
                'street_name', 'street2', 'street_number', 'zip', 'city_id', 'state_id', 'country_id'
            }
            mandatory_fields -= {'street', 'street2', 'city', 'city_id', 'zip', 'phone', 'street_number', 'street_name'}  # Brazil uses the base_extended_address fields added above
        return mandatory_fields

    @route(['/shop/country_info/<model("res.country"):country>'], type='json', auth="public", methods=['POST'],
           website=True, readonly=True)
    def shop_country_info(self, country, address_type, **kw):
        address_fields = country.get_address_fields()
        if address_type == 'billing':
            required_fields = self._get_mandatory_billing_address_fields(country)
        else:
            required_fields = self._get_mandatory_delivery_address_fields(country)
        country
        if country.code == 'DZ':
            return {
                'fields': address_fields,
                'zip_before_city': False,
                'states': [(st.id, st.name, st.code) for st in country.sudo().state_ids],
                'required_fields': list(required_fields),
            }
        else:
            return {
                'fields': address_fields,
                'zip_before_city': (
                        'zip' in address_fields
                        and address_fields.index('zip') < address_fields.index('city')
                ),
                'states': [(st.id, st.name, st.code) for st in country.sudo().state_ids],
                'phone_code': country.phone_code,
                'required_fields': list(required_fields),
            }


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
            partner_sudo.sudo().write({'city_id': city_id.id, 'city': city_id.name})

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
        return {'state_cities': [(c.id, c.name) for c in states]}
