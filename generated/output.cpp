using namespace std;

int heavy_bfs(int target_depth) {
    int count = 0;
    for (int _ = 0; _ < 2000; ++_) {
        queue<int> queue = {0};
        vector<bool> visited(target_depth, false);
        while (!queue.empty()) {
            int node = queue.front();
            queue.pop();
            if (!visited[node]) {
                visited[node] = true;
                count++;
                if (node + 1 < target_depth) {
                    queue.push(node + 1);
                }
                if (node + 2 < target_depth) {
                    queue.push(node + 2);
                }
            }
        }
    }
    return count;
}

int main() {
    cout << heavy_bfs(800) << endl;
    return 0;
}