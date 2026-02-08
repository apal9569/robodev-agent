import argparse
from pathlib import Path
from robodev.agent import RoboDevAgent
from robodev.memory import AgentMemory

def main():
    parser = argparse.ArgumentParser(prog="robodev", description="RoboDev CLI")
    sub = parser.add_subparsers(dest = "cmd", required=True)
    p1 = sub.add_parser("brainstorm", help="Brainstorm robotics approaches")
    p1.add_argument("query", type=str)

    p2 = sub.add_parser("codegen", help="Generate code/config/XML or URDF approaches")
    p2.add_argument("query", type=str)
    p2.add_argument("--lang", default="python", choices=["python", "cpp"], help="Programming language for code generation")
    p2.add_argument("--out", default="./generated", type=str)
    p2.add_argument("--xml", default=None, choices = ["none", "urdf", "sdf"])

    p3 = sub.add_parser("diagnose", help="Analyze build/compile issues")
    p3.add_argument("--log", type=str)

    p4 = sub.add_parser("config", help="Set or View default (stack, sim, lang)")
    p4.add_argument("--set", nargs="*", help='key=value pairs, e.g., stack="ROS2" sim="Gazebo" lang="python"')
    p4.add_argument("--show", action = "store_true")

    p5 = sub.add_parser("i", help="Interactive mode")

    args = parser.parse_args()
    mem = AgentMemory.load()
    agent = RoboDevAgent(memory=mem)

    if args.cmd == "config":
        if args.show:
            print(mem.pretty())
            return
        if args.set:
            for kv in args.set:
                if "=" not in kv:
                    continue
                key, value = kv.split("=")
                mem.config[key.strip()] = value.strip().strip('"').strip("'")
            mem.save()
            print("updated configuration \n")
            print(mem.pretty())
            return
        
    if args.cmd == "brainstorm":
        result = agent.brainstorm(args.query)
        print(result)
        return
    
    if args.cmd == "codegen":
        out_dir = Path(args.out)
        result = agent.codegen(args.query, lang=args.lang, xml=args.xml, out_dir=out_dir)
        print(result)
        return
    
    if args.cmd == "diagnose":
        log_text = Path(args.log).read_text(encoding="utf-8", errors="ignore")
        result = agent.diagnose(log_text)
        print(result)
        return
    
    if args.cmd == "i":
        agent.interactive()
        return
    
if __name__ == "__main__":
    main()