# -*- coding: utf-8 -*-
# Copyright 2019 Lorenzo Battistini
# Copyright 2019 Alessandro Camilli
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "ITA - Bialncio IV direttiva CEE",
    "summary": "Stampe del bilancio riclassificato secondo la IV direttiva CEE",
    "version": "12.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-italy",
    "author": "Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_financial_report",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_view.xml",
        "wizard/report_cee_balance.xml",
        "data/cee_groups.xml",
        "report/templates/cee_balance_report.xml",
        "reports.xml"
    ],
    "qweb": [
    ]
}
