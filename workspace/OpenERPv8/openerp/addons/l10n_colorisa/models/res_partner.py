# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014                                                          #
# David Arnold (El Aleman SAS), Hector Ivan Valencia, Juan Pablo Arias        #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################
import openerp
import re
import codecs
from openerp.osv import orm, fields
from openerp.tools.translate import _

# Define an extencible city model.

class res_country_state_city(orm.Model):
    _name = 'res.country.state.city'
    _description = 'Ciudad'
    #TODO: make sure, that ste and country are consistent, if state is filled.
    _columns = {
        'name': fields.char('Ciudad', size=64, required=True),
        'state_id': fields.many2one('res.country.state', 'Departamento',required=True),
        # 'zip': fields.char('ZIP', size=5),
        # 'phone_prefix': fields.char('Telephone Prefix', size=16),
        'codigo_dane': fields.char('Codigo DANE', size=5,required=True),
        'country_id': fields.many2one('res.country', 'Country',required=True),
        'ciudad_id': fields.one2many('res.partner','ciudad','Ciudad')
        # 'cadaster_code': fields.char('Cadaster Code', size=16),
        # 'web_site': fields.char('Web Site', size=64),
    }

    def onchange_res_city_state(self, cr, uid, ids, state_id, context=None):
        if state_id:
            country_id = self.pool['res.country.state'].browse(cr, uid, state_id, context).country_id.id
            return {'value':{'country_id':country_id}}
        return {}
    
res_country_state_city()

class res_street_abr(orm.Model):
    _name = 'res.street.abr'
    _description = 'Abreviatura Direccion'
    
    _columns = {
        'code': fields.char('Abreviatura', size=64, required=True),
        'name': fields.char('Descripcion', size=64, required=True),
        'abr_id': fields.one2many('res.partner','abr_street','Abreviatura'),
    }
res_street_abr()

class res_partner_co(orm.Model):
    _inherit = 'res.partner'
    
    def get_vat(self, cr, uid, ids,context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.browse(cr, uid, ids)
        res = []
        for records in reads:
            if records.country_id.code and records.ref and records.dv and records.tdoc == '31':
                vat = records.country_id.code + '' +  records.ref + '' + records.dv
                if vat:
                    res.append((records['id'], vat))
            print(self)
        return res
    
    def _get_vat(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_vat(cr, uid, ids, context=context)
        return dict(res) 
    
    
    _columns = {
        'tdoc': fields.selection((('11','Registro civil'), ('12','Tarjeta de identidad'),
                                  ('13','Cédula de ciudadanía'), ('21','Tarjeta de extranjería'),
                                  ('22','Cédula de extranjería'), ('31','NIT'),
                                  ('41','Pasaporte'), ('42','Tipo de documento extranjero'),
                                  ('43','Para uso definido por la DIAN'), ('NU','Número único de identificación'),
                                  ('AS','Adulto sin identificaciómn'), ('MS','Menor sin identificación')),
                                  'Tipo de Documento'),
        'dv': fields.char('dv', size=1, help='Digito de verificación'),
        'lastname': fields.char('lastname', size=25),
        'surname': fields.char('surname', size=25),
        'firstname': fields.char('firstname', size=25),
        'middlename': fields.char('middlename', size=25),
        'ciudad': fields.many2one('res.country.state.city', 'Ciudad'),
        'abr_street':fields.many2one('res.street.abr', 'Abreviatura',select=True),
        'street': fields.char('Street', size=128),
        'state_id': fields.many2one("res.country.state", 'State', ondelete='restrict'),
        'vat' : fields.function(_get_vat, type='char', string='NIF', store=True ),
        'country_id': fields.many2one('res.country', 'Country', ondelete='restrict')
    }

    # change several fields based on the city-field.
    # @api.onchange('city')
    
    _defaults = {
        'tdoc' : '13',
    #    'country_id': lambda self, cr, uid, context: self.pool.get('res.country').browse(cr, uid, self.pool.get('res.country').search(cr, uid, [('code','=','CO')]))[0].id,
    #    'state_id': lambda self, cr, uid, context: self.pool.get('res.country.state').browse(cr, uid, self.pool.get('res.country.state').search(cr, uid, [('code','=','05')]))[0].id,
        }
    
    def onchange_ciudad(self, cr, uid, ids, ciudad, context=None):
        if ciudad:
            state_id = self.pool['res.country.state.city'].browse(cr, uid, ciudad, context).state_id.id
            ciudad_name = self.pool['res.country.state.city'].browse(cr, uid, ciudad, context).name
            return {'value':{'state_id':state_id,'city':ciudad_name}}
        return {}
    
    def onchange_name(self, cr, uid, ids, lastname, surname, firstname, middlename, context=None):
        res = {'value':{}}
        res['value']['name'] =  "%s %s %s %s" % (lastname , surname or '' , firstname , middlename or '')
        return res

    def onchange_tdoc(self, cr, uid, ids, is_company, tdoc, context=None):
        values = {}
        is_company = is_company
        tdoc = tdoc
        if is_company:
            values.update({
            'tdoc' : "31",
            })
        return {'value' : values}
    
    def _address_fields(self, cr, uid, context=None):
        ADDRESS_FIELDS = ( 'abr_street' ,'street', 'ciudad', 'state_id', 'country_id')
        return list(ADDRESS_FIELDS)
    
    def _check_name(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            is_company = record.is_company
            name = record.name
            lastname = record.lastname
            surname = record.surname
            firstname = record.firstname
            middlename = record.middlename
            newname = "%s %s %s %s" % (lastname , surname or '' , firstname , middlename or '')
            if not (lastname or surname or firstname or middlename):
                return True
            elif not is_company and name != newname:
                return False
            elif is_company and (lastname or surname or firstname or middlename):
                return self.write(cr, uid, ids, {'lastname': '', 'surname': '', 'firstname': '', 'middlename':  ''}, context=context)
        return True

# Función para validar que la identificación sea sólo numerica
# Function to validate the numerical identification is only

    def _check_ident_num(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            ref = record.ref
            if ref != False:
                if re.match("^[0-9]+$", ref) == None:
                    return False
        return True
        


# Función para validar que la identificación tenga más de 6 y dígitos y menos de 11
# Function to validate that the identification is more than 6 and less than 11 digits

    def _check_ident(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            # Si utiliza la direccion de la Empresa el ref viene vacio.
            # Evitar esto con break al for.
            if record.use_parent_address:
                break
            else:
                ref = record.ref
                if not ref:
                    return True
                elif len(str(ref)) <6:
                    return False
                elif len(str(ref)) >11:
                    return False
        return True

# Función para evitar número de documento duplicado

    def _check_unique_ident(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids):
            ref = record.ref
            ref_ids = self.search(cr, uid, [('ref', '=', record.ref), ('id', '<>', record.id)])
            if not ref:
                return True
            elif ref_ids:
                return False
        return True

# Función para validar el dígito de verificación
# Function to validate the check digit

    def _check_dv(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            ref = record.ref
            dv = record.dv
            tdoc = record.tdoc
            dvcal = 'dvcal',
            if tdoc == '31':
                if ref != False:
                    if ref.isdigit():
                        b= '0'*(15-len(ref)) + ref
                        vl=list(b)
                        op=(int(vl[0])*71+int(vl[1])*67+int(vl[2])*59+int(vl[3])*53+int(vl[4])*47+int(vl[5])*43+int(vl[6])*41+int(vl[7])*37+int(vl[8])*29+int(vl[9])*23+int(vl[10])*19
                            +int(vl[11])*17+int(vl[12])*13+int(vl[13])*7+int(vl[14])*3)%11

                        if op in (0,1):
                            dvcal = str(op)
                        else:
                            dvcal = str(11-op)
                        if  dv != dvcal:
                            return False
        return True
        
    
    
    def _check_location(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.ciudad.country_id.code == record.country_id.code:
                if record.ciudad.state_id.code != record.state_id.code:
                    return False
            else:
                return False
        return True

    def _check_tdoc(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            is_company = record.is_company
            tdoc = record.tdoc
            if is_company and tdoc != '31':
                return False
        return True

    

# Mensajes de error
# Error Messages

    _constraints = [
        (_check_name, '¡Error! - El nombre no ha sido actualizado, escriba nuevamente el primer apellido', ['name']),
        (_check_ident, '¡Error! Número de identificación debe tener entre 6 y 11 dígitos', ['ref']),
        (_check_unique_ident, '¡Error! Número de identificación ya existe en el sistema', ['ref']),
        (_check_dv, '¡Error! El digito de verificación es incorrecto',['dv']),
        (_check_ident_num, 'Error ! El número de identificación sólo permite números', ['ref']),
        (_check_tdoc, 'Error ! Una empresa solo puede ser identificada con un NIT.', ['tdoc']),
        (_check_location, 'Error !''Localización incoherente', ['ref']),
        ]

    
res_partner_co()
