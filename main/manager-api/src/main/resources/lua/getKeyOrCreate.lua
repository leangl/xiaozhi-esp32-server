local value = redis.call('GET', KEYS[1])
-- Set the value when the key is absent
if not value then
    local result = redis.call('SET', KEYS[1], ARGV[1]) 
    -- Check whether ARGV[2] exists and is greater than zero
    local expireTime = tonumber(ARGV[2])
    if expireTime and expireTime > 0 then
        redis.call('EXPIRE', KEYS[1], expireTime)
    end
end
return value
