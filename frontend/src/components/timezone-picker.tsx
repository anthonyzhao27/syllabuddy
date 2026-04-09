"use client";

import { useMemo, useState } from "react";
import {
  Combobox,
  ComboboxButton,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from "@headlessui/react";
import { ChevronDown, Check, Globe } from "lucide-react";
import { TIMEZONE_GROUPS, findTimezoneOption } from "@/lib/timezones";

interface TimezonePickerProps {
  value: string;
  onChange: (timezone: string) => void;
}

export function TimezonePicker({ value, onChange }: TimezonePickerProps) {
  const [query, setQuery] = useState("");

  const filteredGroups = useMemo(() => {
    if (!query) {
      return TIMEZONE_GROUPS;
    }

    const lowerQuery = query.toLowerCase();
    return TIMEZONE_GROUPS.map((group) => ({
      ...group,
      timezones: group.timezones.filter(
        (tz) =>
          tz.label.toLowerCase().includes(lowerQuery) ||
          tz.value.toLowerCase().includes(lowerQuery) ||
          tz.offset.toLowerCase().includes(lowerQuery)
      ),
    })).filter((group) => group.timezones.length > 0);
  }, [query]);

  const hasResults = filteredGroups.some((group) => group.timezones.length > 0);

  return (
    <Combobox
      value={value}
      onChange={(newValue) => {
        if (newValue) {
          onChange(newValue);
        }
      }}
    >
      <div className="relative">
        <div className="relative">
          <Globe className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-warm-400" />
          <ComboboxInput
            className="w-full rounded-xl border border-warm-200 bg-white py-2 pl-9 pr-10 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
            displayValue={(val: string) => {
              const option = findTimezoneOption(val);
              return option ? `${option.label} (${option.offset})` : val;
            }}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search timezones..."
          />
          <ComboboxButton className="absolute inset-y-0 right-0 flex items-center pr-3">
            <ChevronDown className="h-4 w-4 text-warm-400" aria-hidden="true" />
          </ComboboxButton>
        </div>

        <ComboboxOptions className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-xl border border-warm-200 bg-white py-1 text-sm shadow-lg focus:outline-none">
          {!hasResults && (
            <div className="px-4 py-2 text-warm-500">No timezones found</div>
          )}
          {filteredGroups.map((group) =>
            group.timezones.length > 0 ? (
              <div key={group.region}>
                <div className="sticky top-0 z-10 bg-white border-b border-warm-100 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-warm-500">
                  {group.region}
                </div>
                {group.timezones.map((tz) => (
                  <ComboboxOption
                    key={tz.value}
                    value={tz.value}
                    className="group relative cursor-pointer select-none py-2 pl-10 pr-4 text-warm-700 data-[focus]:bg-mint-50 data-[focus]:text-mint-900"
                  >
                    {({ selected }) => (
                      <>
                        <span
                          className={`block truncate ${selected ? "font-medium" : "font-normal"}`}
                        >
                          {tz.label}
                          <span className="ml-2 text-warm-400">
                            {tz.offset}
                          </span>
                        </span>
                        {selected && (
                          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-mint-600">
                            <Check className="h-4 w-4" aria-hidden="true" />
                          </span>
                        )}
                      </>
                    )}
                  </ComboboxOption>
                ))}
              </div>
            ) : null
          )}
        </ComboboxOptions>
      </div>
    </Combobox>
  );
}
