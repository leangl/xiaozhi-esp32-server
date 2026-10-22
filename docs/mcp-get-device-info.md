# Access device information from an MCP method

1. Copy `xiaozhi-server/agent-base-prompt.txt` to `data/.agent-base-prompt.txt`.
2. In the copied file's `<context>` section, add the device ID placeholder:

```text
- **Device ID:** {{device_id}}
```

The context section should then include the same live context values as before. Use the supplied information rather than calling tools to query it:

```text
<context>
[Important: the following information is provided in real time. Use it directly without querying tools.]
- **Device ID:** {{device_id}}
- **Current time:** {{current_time}}
- **Today's date:** {{today_date}} ({{today_weekday}})
- **Today's lunar date:** {{lunar_date}}
- **User's city:** {{local_address}}
- **Local weather for the next 7 days:** {{weather_info}}
</context>
```

3. In `data/.config.yaml`, change the prompt-template setting from:

```
prompt_template: agent-base-prompt.txt
```

to:

```
prompt_template: data/.agent-base-prompt.txt
```

4. Restart your `xiaozhi-server` service.
5. Add a parameter named `device_id`, with type `string` and description “Device ID”, to your MCP method.
6. Wake Xiaozhi again, ask it to call the method, and check that your method receives the device ID.
