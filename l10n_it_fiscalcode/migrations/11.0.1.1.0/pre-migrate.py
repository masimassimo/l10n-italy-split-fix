def migrate(cr, version):
    if not version:
        return

    cr.execute("DROP VIEW IF EXISTS res_city_it_code_province;")
