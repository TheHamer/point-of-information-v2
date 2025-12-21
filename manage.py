#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import json
import time

# #region agent log
log_path = os.path.join(os.path.dirname(__file__), '.cursor', 'debug.log')
try:
    with open(log_path, 'a') as f:
        f.write(json.dumps({
            'id': f'log_{int(time.time() * 1000)}_manage',
            'timestamp': int(time.time() * 1000),
            'location': 'manage.py:7',
            'message': 'manage.py main() entry',
            'data': {'argv': sys.argv},
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'D'
        }) + '\n')
except Exception:
    pass
# #endregion


def main():
    """Run administrative tasks."""
    # #region agent log
    try:
        with open(log_path, 'a') as f:
            f.write(json.dumps({
                'id': f'log_{int(time.time() * 1000)}_manage_main',
                'timestamp': int(time.time() * 1000),
                'location': 'manage.py:25',
                'message': 'Before execute_from_command_line',
                'data': {'command': sys.argv[1] if len(sys.argv) > 1 else 'none'},
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'D'
            }) + '\n')
    except Exception:
        pass
    # #endregion
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'debatesite.settings')
    try:
        import django
        django.setup()
        # #region agent log
        try:
            from django.db import connection
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_user, current_database();")
                row = cursor.fetchone()
                with open(log_path, 'a') as f:
                    f.write(json.dumps({
                        'id': f'log_{int(time.time() * 1000)}_db_conn',
                        'timestamp': int(time.time() * 1000),
                        'location': 'manage.py:51',
                        'message': 'Database connection established',
                        'data': {
                            'current_user': row[0] if row else 'unknown',
                            'current_database': row[1] if row else 'unknown'
                        },
                        'sessionId': 'debug-session',
                        'runId': 'run1',
                        'hypothesisId': 'D'
                    }) + '\n')
                cursor.execute("""
                    SELECT nspname, nspowner::regrole, 
                           has_schema_privilege(current_user, nspname, 'USAGE') as has_usage,
                           has_schema_privilege(current_user, nspname, 'CREATE') as has_create
                    FROM pg_namespace 
                    WHERE nspname = 'public';
                """)
                schema_row = cursor.fetchone()
                if schema_row:
                    with open(log_path, 'a') as f:
                        f.write(json.dumps({
                            'id': f'log_{int(time.time() * 1000)}_schema_perm',
                            'timestamp': int(time.time() * 1000),
                            'location': 'manage.py:70',
                            'message': 'Public schema permissions check',
                            'data': {
                                'schema_name': schema_row[0],
                                'schema_owner': str(schema_row[1]),
                                'has_usage': schema_row[2],
                                'has_create': schema_row[3]
                            },
                            'sessionId': 'debug-session',
                            'runId': 'run1',
                            'hypothesisId': 'A'
                        }) + '\n')
        except Exception as e:
            try:
                with open(log_path, 'a') as f:
                    f.write(json.dumps({
                        'id': f'log_{int(time.time() * 1000)}_db_check_err',
                        'timestamp': int(time.time() * 1000),
                        'location': 'manage.py:85',
                        'message': 'Database permission check failed',
                        'data': {'error': str(e), 'error_type': type(e).__name__},
                        'sessionId': 'debug-session',
                        'runId': 'run1',
                        'hypothesisId': 'A'
                    }) + '\n')
            except Exception:
                pass
        # #endregion
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # #region agent log
    try:
        with open(log_path, 'a') as f:
            f.write(json.dumps({
                'id': f'log_{int(time.time() * 1000)}_before_exec',
                'timestamp': int(time.time() * 1000),
                'location': 'manage.py:80',
                'message': 'About to execute_from_command_line',
                'data': {},
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'D'
            }) + '\n')
    except Exception:
        pass
    # #endregion
    try:
        execute_from_command_line(sys.argv)
    except Exception as e:
        # #region agent log
        try:
            with open(log_path, 'a') as f:
                f.write(json.dumps({
                    'id': f'log_{int(time.time() * 1000)}_exec_err',
                    'timestamp': int(time.time() * 1000),
                    'location': 'manage.py:90',
                    'message': 'execute_from_command_line exception',
                    'data': {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'error_args': str(e.args) if hasattr(e, 'args') else 'none'
                    },
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'A'
                }) + '\n')
        except Exception:
            pass
        # #endregion
        raise


if __name__ == '__main__':
    main()
