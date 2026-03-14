def heavy_bfs(target_depth):
    count = 0
    # Run the BFS 2000 times to simulate a massive workload
    for _ in range(2000):
        queue = [0]
        visited = [False] * target_depth
        
        while len(queue) > 0:
            node = queue.pop(0)
            if not visited[node]:
                visited[node] = True
                count += 1
                # Add dummy children
                if node + 1 < target_depth:
                    queue.append(node + 1)
                if node + 2 < target_depth:
                    queue.append(node + 2)
                    
    return count

if __name__ == "__main__":
    # This will make Python sweat for a few seconds
    print(heavy_bfs(800))