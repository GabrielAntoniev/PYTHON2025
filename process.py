import sys
import argparse
import psutil as ps
import os 

def list_processes(sort_by, desc_order):
    process_list = []

    for proc in ps.process_iter(['pid', 'name', 'exe', 'cmdline', 'memory_info']):
        try:
            p_info = proc.info
            pid = int(p_info['pid'])
            name = str(p_info['name'])
            path = str(p_info['exe']) if p_info['exe'] else ''
            cmdline = " ".join(p_info['cmdline']) if p_info['cmdline'] else ''
            mem_mb = p_info['memory_info'].rss / 1048576  #1024*1024
            cpu_usage = proc.cpu_percent(interval=0.01)
            
            process_list.append({
                'pid': pid,
                'name': name,
                'path': path,
                'cmdline': cmdline,
                'mem': mem_mb,
                'cpu': cpu_usage
            })

        except (ps.NoSuchProcess, ps.AccessDenied, ps.ZombieProcess):
            continue

    if sort_by == 'cpu':
        process_list.sort(key=lambda x: x['cpu'], reverse=desc_order)
    elif sort_by == 'mem':
        process_list.sort(key=lambda x: x['mem'], reverse=desc_order)
    elif sort_by == 'pid':
        process_list.sort(key=lambda x: x['pid'], reverse=desc_order)
    
    print("-" * 100)
    print(f"{'PID':<8} {'Name':<21} {'CPU%':<8} {'MEM':<10} {'PATH':<25} {'CMDLINE'}")
    print("-" * 100)

    for p in process_list:
        pid_str = str(p['pid'])
        name_str = p['name'][:20] 
        cpu_str = f"{p['cpu']:.1f}"
        mem_str = f"{p['mem']:.1f}"        
        path_str = p['path']
        if len(path_str) > 24:
            path_str = "..." + path_str[-21:]
            
        cmd_str = p['cmdline'][:70]

        print(f"{pid_str:<8} {name_str:<20} {cpu_str:<8} {mem_str:<10} {path_str:<25} {cmd_str}")



def run_process(path, args=None, cwd=None):
    try:

        if cwd and not os.path.isabs(path):
            full_path = os.path.join(cwd, path)
        else:
            full_path = path
        
        full_path = os.path.expanduser(full_path)

        if not os.path.exists(full_path):
            print(f"Error: Executable not found: {full_path}", file=sys.stderr)
            exit(1)
        
        cmd = [full_path]
        if full_path.endswith('.py'):
            cmd = ['python3', full_path]
        elif full_path.endswith('.sh'):
            cmd = ['bash', full_path]

        if args:
            cmd.extend(args)
        
        print(cmd)
        proc = ps.Popen(
            cmd,
            cwd=cwd,
            stdout=ps.subprocess.DEVNULL,
            stderr=ps.subprocess.DEVNULL,
            stdin=ps.subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True
        )
        
        print(f"Process started with PID: {proc.pid}")
        return 0
        
    except FileNotFoundError:
        print(f"Error: Executable not found: {path}", file=sys.stderr)
        exit(1)
    except PermissionError:
        print(f"Error: Permission denied: {path}", file=sys.stderr)
        exit(2)
    except Exception as e:
        print(f"Error starting process: {e}", file=sys.stderr)
        exit(3)

def kill_process(pid):
    try:
        proc = ps.Process(pid)        
        proc.terminate()
        
        try:
            proc.wait(timeout=3)
            print(f"Process {pid} terminated successfully")
            return 0
        except ps.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=1)
            print(f"Process {pid} killed (forced)")
            return 0
            
    except ps.NoSuchProcess:
        print(f"Error: PID not found: {pid}", file=sys.stderr)
        exit(4)
    except ps.AccessDenied:
        print(f"Error: Insufficient permission for PID {pid}", file=sys.stderr)
        exit(5)
    except Exception as e:
        print(f"Error killing process {pid}: {e}", file=sys.stderr)
        exit(6)
    

def suspend_process(pid):
    try:
        proc = ps.Process(pid)        
        if proc.status() == ps.STATUS_STOPPED:
            print(f"Process {pid} is already suspended")
            exit(7)
        
        proc.suspend()
        print(f"Process {pid} suspended")
        return 0
        
    except ps.NoSuchProcess:
        print(f"Error: PID not found: {pid}", file=sys.stderr)
        exit(4)
    except ps.AccessDenied:
        print(f"Error: Insufficient permission for PID {pid}", file=sys.stderr)
        exit(5)
    except Exception as e:
        print(f"Error suspending process {pid}: {e}", file=sys.stderr)
        exit(8)
    

def resume_process(pid):
    try:
        proc = ps.Process(pid)        
        if proc.status() != ps.STATUS_STOPPED:
            print(f"Process {pid} is not suspended")
            return 0
        
        proc.resume()
        print(f"Process {pid} resumed")
        return 0
        
    except ps.NoSuchProcess:
        print(f"Error: PID not found: {pid}", file=sys.stderr)
        exit(4)
    except ps.AccessDenied:
        print(f"Error: Insufficient permission for PID {pid}", file=sys.stderr)
        exit(5)
    except Exception as e:
        print(f"Error resuming process {pid}: {e}", file=sys.stderr)
        exit(9)


#############################MAIN#######################################

parser = argparse.ArgumentParser(description="The Super Mega Jmeker Process Manager")
subparsers = parser.add_subparsers(dest="command", help="Available commands")

#pentru view
view_parser = subparsers.add_parser("view", help="List all processes")
view_parser.add_argument("--sort", choices=['cpu', 'mem', 'pid'], default='pid', help="Sort by cpu, mem, or pid")
view_parser.add_argument("--desc", action="store_true", help="Sort in descending order")

#pentru run
run_parser = subparsers.add_parser('run', help='Start a new process')
run_parser.add_argument('path', help='Path to executable')
run_parser.add_argument('args', nargs='*', help='Arguments to pass to the process')
run_parser.add_argument('--cwd', help='Working directory for the process')
    
#pentru kill
kill_parser = subparsers.add_parser('kill', help='Terminate a process')
kill_parser.add_argument('pid', type=int, help='Process ID to kill')

#pentru suspend
suspend_parser = subparsers.add_parser('suspend', help='Suspend (pause) a process')
suspend_parser.add_argument('pid', type=int, help='Process ID to suspend')

#pentru resume
resume_parser = subparsers.add_parser('resume', help='Resume a suspended process')
resume_parser.add_argument('pid', type=int, help='Process ID to resume')

args = parser.parse_args()

if args.command == "view":
    list_processes(args.sort, args.desc)
elif args.command == 'run':
    run_process(args.path, args.args, args.cwd)
elif args.command == 'kill':
    kill_process(args.pid)
elif args.command == 'suspend':
    suspend_process(args.pid)
elif args.command == 'resume':
    resume_process(args.pid)
else:
    parser.print_help()