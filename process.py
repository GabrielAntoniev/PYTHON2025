import sys
import argparse
import psutil as ps

def list_processes(sort_by, desc_order):
    process_list = []

    for proc in ps.process_iter(['pid', 'name', 'exe', 'cmdline', 'memory_info']):
        try:
            p_info = proc.info
            pid = str(p_info['pid'])
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



#############################MAIN#######################################

parser = argparse.ArgumentParser(description="The Super Mega Jmeker Process Manager")
subparsers = parser.add_subparsers(dest="command", help="Available commands")

#pentru view
view_parser = subparsers.add_parser("view", help="List all processes")
view_parser.add_argument("--sort", choices=['cpu', 'mem', 'pid'], default='pid', help="Sort by cpu, mem, or pid")
view_parser.add_argument("--desc", action="store_true", help="Sort in descending order")
    
args = parser.parse_args()

if args.command == "view":
    list_processes(args.sort, args.desc)
else:
    parser.print_help()