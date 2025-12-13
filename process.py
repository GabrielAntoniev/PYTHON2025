import sys
import argparse
import subprocess
import psutil as ps

def list_processes(sort_by, desc_order):
    process_list = []

    for proc in ps.process_iter(['pid', 'name', 'exe', 'cmdline', 'memory_info']):
        try:
            p_info = proc.info
            pid = int(p_info['pid'])
            name = str(p_info['name'])
            path = str(p_info['exe'])
            cmdline = " ".join(p_info['cmdline'])
            mem_mb = p_info['memory_info'].rss / 1048576 #1024*1024
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
        cmd = [path]
        if args:
            cmd.extend(args)
        
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        
        print(f"Process started with PID: {proc.pid}")
        return 0
        
    except FileNotFoundError:
        print(f"Error: Executable not found: {path}", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"Error: Permission denied: {path}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error starting process: {e}", file=sys.stderr)
        return 3


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
        return 4
    except ps.AccessDenied:
        print(f"Error: Insufficient permission for PID {pid}", file=sys.stderr)
        return 5
    except Exception as e:
        print(f"Error killing process {pid}: {e}", file=sys.stderr)
        return 6


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
    
args = parser.parse_args()

if args.command == "view":
    list_processes(args.sort, args.desc)
elif args.command == 'run':
    run_process(args.path, args.args, args.cwd)
elif args.command == 'kill':
    kill_process(args.pid)
else:
    parser.print_help()