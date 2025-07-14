def getMaxNoOfFrogs(stones, k, w):
    rem = k - len(stones) % k
    stones.extend([10**5]*rem) 
    n = len(stones)

    frogs = [0]*n
    for i in range(k):
        frogs[i] = stones[i]
        stones[i] = 0

    s1, e1 = 0, k-1
    s2, e2 = k, k+k-1
    while s2 < n:
        f, s = e1, e2
        while f >= s1 and s >= s2:
            if stones[s] == 0 or s - f > k :    s -= 1  
            elif frogs[f] == 0:       f -= 1
            elif stones[s] > frogs[f]:
                frogs[s] += frogs[f]
                stones[s] -= frogs[f]
                frogs[f] = 0
            elif stones[s] < frogs[f]:
                frogs[s] += stones[s]
                frogs[f] -= stones[s]
                stones[s] = 0
            else:
                frogs[s] += stones[s]
                stones[s] = 0
                frogs[f] = 0
        s1, e1 = s1+k, e1+k
        s2, e2 = s2+k, e2+k


    maxFrogs = 0
    for i in range(n-1, k-1, -1):
        maxFrogs += frogs[i]
    
    return maxFrog
