# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration

from guardian.compat import user_model_label
from guardian.compat import get_user_model

User = get_user_model()

def get_user_pk_field_fully_qualified_name():
    pk_field = User._meta.pk
    module = pk_field.__class__.__module__
    if module is None:
        return pk_field.__class__.__name__
    return module + '.' + pk_field.__class__.__name__


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'GroupObjectPermission.object_pk'
        db.alter_column('guardian_groupobjectpermission', 'object_pk', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'UserObjectPermission.object_pk'
        db.alter_column('guardian_userobjectpermission', 'object_pk', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Removing unique constraint on 'UserObjectPermission', fields ['object_id', 'user', 'content_type', 'permission']
        db.delete_unique('guardian_userobjectpermission', ['object_id', 'user_id', 'content_type_id', 'permission_id'])

        # Removing unique constraint on 'GroupObjectPermission', fields ['group', 'object_id', 'content_type', 'permission']
        db.delete_unique('guardian_groupobjectpermission', ['group_id', 'object_id', 'content_type_id', 'permission_id'])

        # Adding unique constraint on 'GroupObjectPermission', fields ['object_pk', 'group', 'content_type', 'permission']
        db.create_unique('guardian_groupobjectpermission', ['object_pk', 'group_id', 'content_type_id', 'permission_id'])

        # Adding unique constraint on 'UserObjectPermission', fields ['object_pk', 'user', 'content_type', 'permission']
        db.create_unique('guardian_userobjectpermission', ['object_pk', 'user_id', 'content_type_id', 'permission_id'])


    def backwards(self, orm):

        # Changing field 'GroupObjectPermission.object_pk'
        db.alter_column('guardian_groupobjectpermission', 'object_pk', self.gf('django.db.models.fields.TextField')())

        # Changing field 'UserObjectPermission.object_pk'
        db.alter_column('guardian_userobjectpermission', 'object_pk', self.gf('django.db.models.fields.TextField')())

        # Removing unique constraint on 'UserObjectPermission', fields ['object_pk', 'user', 'content_type', 'permission']
        db.delete_unique('guardian_userobjectpermission', ['object_pk', 'user_id', 'content_type_id', 'permission_id'])

        # Removing unique constraint on 'GroupObjectPermission', fields ['object_pk', 'group', 'content_type', 'permission']
        db.delete_unique('guardian_groupobjectpermission', ['object_pk', 'group_id', 'content_type_id', 'permission_id'])

        # Adding unique constraint on 'GroupObjectPermission', fields ['group', 'object_id', 'content_type', 'permission']
        db.create_unique('guardian_groupobjectpermission', ['group_id', 'object_id', 'content_type_id', 'permission_id'])

        # Adding unique constraint on 'UserObjectPermission', fields ['object_id', 'user', 'content_type', 'permission']
        db.create_unique('guardian_userobjectpermission', ['object_id', 'user_id', 'content_type_id', 'permission_id'])


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        user_model_label: {
            'Meta': {'object_name': user_model_label.split('.')[-1], 'db_table': "'%s'" % User._meta.db_table},
            User._meta.pk.attname: (
                get_user_pk_field_fully_qualified_name(), [],
                {'primary_key': 'True',
                'db_column': "'%s'" % User._meta.pk.column}
            ),
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'guardian.groupobjectpermission': {
            'Meta': {'unique_together': "(['group', 'permission', 'content_type', 'object_pk'],)", 'object_name': 'GroupObjectPermission'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_pk': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'permission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Permission']"})
        },
        'guardian.userobjectpermission': {
            'Meta': {'unique_together': "(['user', 'permission', 'content_type', 'object_pk'],)", 'object_name': 'UserObjectPermission'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_pk': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'permission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Permission']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s']" % user_model_label})
        }
    }

    complete_apps = ['guardian']
