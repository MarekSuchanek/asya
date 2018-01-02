import sys
from datetime import datetime

import click

from .supervisor import AsyaSupervisor
from .logic import gather_acquaintances
from .exceptions import AsyaException


_user_involvement = ('author', 'involves', 'mentions',
                     'assigned', 'commenter')

API_SEARCH_LIMIT = 1000


def create_search_specs(username, sort, order, text, involvement, query_opts):
    """Create GitHub issues search specification (params dict)"""
    query_opts[involvement] = username
    query = '+'.join(['{}:{}'.format(k, v)
                      for k, v in query_opts.items()
                      if v is not None])
    if text is not None:
        query = '+'.join([text, query])

    search_specs = {'q': query}
    if sort is not None:
        search_specs['sort'] = sort
    if order is not None:
        search_specs['order'] = order

    return search_specs


def setup_progressbar(supervisor):
    """Setup progressbar for given supervisor"""
    supervisor.data['skipped'] = 0

    def add_skipped(headers):
        supervisor.data['skipped'] += 1

    def report_skipped():
        if supervisor.data['skipped'] > 0:
            click.echo('{} error(s) 404 skipped'.format(
                supervisor.data['skipped']
            ))

    supervisor.data['waiting'] = 0
    supervisor.data['bar_message'] = None

    def show_message(item):
        if supervisor.data['bar_message'] is None:
            return ''
        return '({})'.format(supervisor.data['bar_message'])

    supervisor.data['bar'] = click.progressbar(
        length=0, label='Processing issues', show_pos=True,
        fill_char='\u2588', empty_char='\u2591',
        item_show_func=show_message,
        bar_template='%(label)s:  %(bar)s %(info)s'
    )

    def init_bar(first_result, page):
        if page == 1:
            nresults = min(API_SEARCH_LIMIT, first_result['total_count'])
            if first_result['total_count'] > API_SEARCH_LIMIT:
                click.echo('{} issue(s) will be processed (due to API limits,'
                           ' although there are {} issues)'.format(
                    API_SEARCH_LIMIT, first_result['total_count']
                ))
            supervisor.data['bar'].length = nresults
            supervisor.data['bar'].entered = True
            supervisor.data['bar'].render_progress()

    def increase_bar(issue):
        supervisor.data['bar'].update(1)

    def finish_bar():
        supervisor.data['bar'].finish()
        supervisor.data['bar'].render_finish()

    def waiting_phase_change(active, headers):
        to_time = int(headers['X-RateLimit-Reset'])
        if active and to_time > supervisor.data['waiting']:
            supervisor.data['waiting'] = to_time
            supervisor.data['bar_message'] = 'waiting [{}]'.format(
                datetime.fromtimestamp(to_time).strftime('%Y-%m-%d %H:%M:%S')
            )
            supervisor.data['bar'].render_progress()
        if not active and to_time == supervisor.data['waiting']:
            supervisor.data['waiting'] = 0
            supervisor.data['bar_message'] = None
            supervisor.data['bar'].render_progress()

    supervisor.callbacks['issues_search_page'].append(init_bar)
    supervisor.callbacks['issue'].append(increase_bar)
    supervisor.callbacks['skip'].append(add_skipped)
    supervisor.callbacks['wait'].append(waiting_phase_change)
    supervisor.callbacks['finish_successful'].append(finish_bar)
    supervisor.callbacks['finish_errored'].append(finish_bar)
    supervisor.callbacks['finish_successful'].append(report_skipped)
    supervisor.callbacks['finish_errored'].append(report_skipped)


def setup_info_msgs(supervisor):
    """Setup text info printing for given supervisor"""
    supervisor.data['waiting'] = 0
    supervisor.data['skipped'] = 0

    def add_skipped(headers):
        supervisor.data['skipped'] += 1

    def report_skipped():
        if supervisor.data['skipped'] > 0:
            click.echo('{} error(s) 404 skipped'.format(
                supervisor.data['skipped']
            ))

    def print_count(first_result, page):
        if page == 1:
            if first_result['total_count'] > API_SEARCH_LIMIT:
                click.echo('{} issue(s) will be processed (due to API limits,'
                           ' although there are {} issues)'.format(
                    API_SEARCH_LIMIT, first_result['total_count']
                ))
            else:
                click.echo('{} issue(s) to be processed...'.format(
                    first_result['total_count']
                ))

    def waiting_phase_change(active, headers):
        to_time = int(headers['X-RateLimit-Reset'])
        if active and to_time > supervisor.data['waiting']:
            supervisor.data['waiting'] = to_time
            click.echo('Waiting for API rate limit reset until {}'.format(
                datetime.fromtimestamp(to_time).strftime('%Y-%m-%d %H:%M:%S')
            ))
        if not active and to_time == supervisor.data['waiting']:
            supervisor.data['waiting'] = 0
            click.echo('Resuming working after wait')

    supervisor.callbacks['issues_search_page'].append(print_count)
    supervisor.callbacks['wait'].append(waiting_phase_change)
    supervisor.callbacks['skip'].append(add_skipped)
    supervisor.callbacks['finish_successful'].append(report_skipped)
    supervisor.callbacks['finish_errored'].append(report_skipped)


def print_result(result):
    """Print Asya result nicely"""
    if result is None:
        click.secho('Result is None!', fg='red')
        return
    elif len(result) == 0:
        click.echo('No results to print...')
        return
    d = [(k, result[k]) for k in sorted(result, key=result.get, reverse=True)]
    uwidth = max([len(username) for username, _ in d])
    cwidth = max([len(str(count)) for _, count in d])
    for username, count in d:
        click.echo(
            '{u:{uw}} = {c:{cw}}'.format(
                u=username, uw=uwidth,
                c=count, cw=cwidth
            )
        )


def no_print(*args, **kwargs):
    """Dummy method for not actually printing anything"""
    pass


@click.command()
@click.argument('username')
@click.option('-i', '--involvement', type=click.Choice(_user_involvement),
              default='author', help='How is given user involved in issues.')
@click.option('--text', help='Text to filter issues.')
@click.option('--in', type=click.Choice(['title', 'body', 'comments']),
              help='In what should be text searched.')
@click.option('--type', type=click.Choice(['issue', 'pr']),
              help='Restriction to just issues or just PRs.')
@click.option('--state', type=click.Choice(['open', 'closed']),
              help='Restriction to just issues or just PRs.')
@click.option('--created',
              help='Date expression to filter by created date.')
@click.option('--updated',
              help='Date expression to filter by updated date.')
@click.option('--label',
              help='String to filter by label.')
@click.option('--language',
              help='String to filter by language.')
@click.option('--sort', type=click.Choice(['comments', 'created', 'updated']),
              help='Sort search results (important for >1000 results).')
@click.option('--order', type=click.Choice(['asc', 'desc']),
              help='Sort order of results (important for >1000 results).')
@click.option('-t', '--token', default=None,
              envvar='GITHUB_TOKEN', help='Personal GitHub token.')
@click.option('-w', '--wait-rate-limit', is_flag=True,
              help='Wait for rate limit reset if needed.')
@click.option('-s', '--skip-404', is_flag=True,
              help='Skip not-found GitHub resources (such as disabled repos).')
@click.option('-b', '--progress-bar', is_flag=True,
              help='Toggle progress bar (default false).')
@click.option('--info/--no-info', default=True,
              help='Toggle info texts (default true).')
@click.option('--api-endpoint', default='https://api.github.com',
              help='How is given user involved in issues.')
@click.option('--debug', is_flag=True, default=False,
              help='Debug mode (not catching other exceptions).')
@click.version_option('0.1-alt')
def main(username, token, wait_rate_limit, sort, order, progress_bar, info,
         skip_404, text, involvement, api_endpoint, debug, **query_opts):
    """Asya Command Line Interface (via :mod:`click`)"""
    search_specs = create_search_specs(username, sort, order, text,
                                       involvement, query_opts)
    supervisor = AsyaSupervisor(api_endpoint, token, wait_rate_limit, skip_404)

    print_info = no_print

    if progress_bar:
        setup_progressbar(supervisor)
    elif info:
        setup_info_msgs(supervisor)
    if info:
        print_info = click.secho

    if debug:
        result = gather_acquaintances(search_specs, supervisor)
        supervisor.report_finish_successful()
        print_info('Asya gathered acquaintances successfully:',
                   fg='green', bold=True, err=True)
        print_result(result)
    else:
        try:
            result = gather_acquaintances(search_specs, supervisor)
            supervisor.report_finish_successful()
            print_info('Asya gathered acquaintances successfully:',
                       fg='green', bold=True, err=True)
            print_result(result)
        except AsyaException as err:
            supervisor.report_finish_errored()
            print_info('Asya ended with communication error:',
                       fg='red', bold=True, err=True)
            click.echo(err.message, err=True)
            sys.exit(7)
        except Exception as err:
            supervisor.report_finish_errored()
            print_info('Asya ended with fatal error:',
                       fg='red', bold=True, err=True)
            click.echo(err.__class__.__name__, err=True)
            sys.exit(10)
