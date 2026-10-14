def migrate(cr, version):
    cr.execute(
        """
        UPDATE operations_control_item
           SET state = 'closed'
         WHERE state = 'done'
        """
    )
