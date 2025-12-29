import React, { useState } from 'react';
import {
  Wifi,
  WifiOff,
  CheckCircle2,
  Smartphone,
  Loader2,
  XCircle,
  Clock,
  Pencil,
  Trash2,
  Unplug,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ConfirmDialog } from './ConfirmDialog';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { useTranslation } from '../lib/i18n-context';
import type { AgentStatus } from '../api';

interface DeviceCardProps {
  id: string;
  serial: string;
  model: string;
  status: string;
  connectionType?: string;
  alias?: string | null;
  agent?: AgentStatus | null;
  isActive: boolean;
  onClick: () => void;
  onConnectWifi?: () => Promise<void>;
  onDisconnectWifi?: () => Promise<void>;
  onDisconnectAll?: () => Promise<void>;
  onRename?: (alias: string) => Promise<void>;
  onDelete?: () => Promise<void>;
}

export function DeviceCard({
  id,
  serial,
  model,
  status,
  connectionType,
  alias,
  agent,
  isActive,
  onClick,
  onConnectWifi,
  onDisconnectWifi,
  onDisconnectAll,
  onRename,
  onDelete,
}: DeviceCardProps) {
  const t = useTranslation();
  const isOnline = status === 'device';
  const isUsb = connectionType === 'usb';
  const isRemote = connectionType === 'remote';
  const [loading, setLoading] = useState(false);
  const [showWifiConfirm, setShowWifiConfirm] = useState(false);
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
  const [showDisconnectAllConfirm, setShowDisconnectAllConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showRenameDialog, setShowRenameDialog] = useState(false);
  const [editValue, setEditValue] = useState(alias || '');

  const displayName = alias || model || t.deviceCard.unknownDevice;

  const handleWifiClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (loading || !onConnectWifi) return;
    setShowWifiConfirm(true);
  };

  const handleDisconnectClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (loading || !onDisconnectWifi) return;
    setShowDisconnectConfirm(true);
  };

  const handleDisconnectAllClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (loading || !onDisconnectAll) return;
    setShowDisconnectAllConfirm(true);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (loading || !onDelete) return;
    setShowDeleteConfirm(true);
  };

  const handleEditClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditValue(alias || '');
    setShowRenameDialog(true);
  };

  const handleDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!onRename) return;
    setEditValue(alias || '');
    setShowRenameDialog(true);
  };

  const handleSaveRename = async () => {
    if (!onRename) return;
    setLoading(true);
    try {
      await onRename(editValue);
      setShowRenameDialog(false);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmWifi = async () => {
    setShowWifiConfirm(false);
    setLoading(true);
    try {
      if (onConnectWifi) {
        await onConnectWifi();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDisconnect = async () => {
    setShowDisconnectConfirm(false);
    setLoading(true);
    try {
      if (onDisconnectWifi) {
        await onDisconnectWifi();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDisconnectAll = async () => {
    setShowDisconnectAllConfirm(false);
    setLoading(true);
    try {
      if (onDisconnectAll) {
        await onDisconnectAll();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDelete = async () => {
    setShowDeleteConfirm(false);
    setLoading(true);
    try {
      if (onDelete) {
        await onDelete();
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div
        onClick={onClick}
        role="button"
        tabIndex={0}
        onKeyDown={e => {
          if (e.key === 'Enter' || e.key === ' ') {
            onClick();
          }
        }}
        className={`
          group relative w-full text-left p-4 rounded-xl transition-all duration-200 cursor-pointer
          border-2
          ${
            isActive
              ? 'bg-slate-50 border-[#1d9bf0] dark:bg-slate-800/50 dark:border-[#1d9bf0]'
              : 'bg-white border-transparent hover:border-slate-200 dark:bg-slate-900 dark:hover:border-slate-700'
          }
        `}
      >
        {/* Active indicator bar */}
        {isActive && (
          <div className="absolute left-0 top-2 bottom-2 w-1 bg-[#1d9bf0] rounded-r" />
        )}

        <div className="flex items-center gap-3 pl-2">
          {/* Status indicator */}
          <div
            className={`relative flex-shrink-0 ${
              isOnline ? 'status-online' : 'status-offline'
            } w-3 h-3 rounded-full transition-all ${
              isActive ? 'scale-110' : ''
            }`}
          />

          {/* Device icon and info */}
          <div className="flex-1 min-w-0 flex flex-col justify-center gap-0.5">
            <div className="flex items-center gap-2">
              <Smartphone
                className={`w-4 h-4 flex-shrink-0 ${
                  isActive
                    ? 'text-[#1d9bf0]'
                    : 'text-slate-400 dark:text-slate-500'
                }`}
              />
              <span
                onDoubleClick={handleDoubleClick}
                className={`font-semibold text-sm truncate cursor-pointer ${
                  isActive
                    ? 'text-slate-900 dark:text-slate-100'
                    : 'text-slate-700 dark:text-slate-300'
                } ${onRename ? 'hover:text-[#1d9bf0] dark:hover:text-[#1d9bf0]' : ''}`}
                title={onRename ? t.deviceCard.doubleClickToRename : undefined}
              >
                {displayName}
              </span>
              {onRename && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleEditClick}
                  className="h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-[#1d9bf0]"
                >
                  <Pencil className="w-3 h-3" />
                </Button>
              )}
            </div>
            <span
              className={`text-xs font-mono truncate ${
                isActive
                  ? 'text-slate-500 dark:text-slate-400'
                  : 'text-slate-400 dark:text-slate-500'
              }`}
            >
              {alias ? model : id}
            </span>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1 flex-shrink-0">
            {/* Action buttons - only show on hover */}
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {isUsb && onConnectWifi && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleWifiClick}
                  disabled={loading}
                  className={`h-7 w-7 rounded-full ${
                    isActive
                      ? 'bg-[#1d9bf0]/10 text-[#1d9bf0] hover:bg-[#1d9bf0]/20'
                      : 'text-slate-400 dark:text-slate-500 hover:text-[#1d9bf0] dark:hover:text-[#1d9bf0] hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                  title={t.deviceCard.connectViaWifi}
                >
                  {loading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Wifi className="w-3.5 h-3.5" />
                  )}
                </Button>
              )}

              {isRemote && onDisconnectWifi && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleDisconnectClick}
                  disabled={loading}
                  className={`h-7 w-7 rounded-full ${
                    isActive
                      ? 'bg-red-500/10 text-red-500 hover:bg-red-500/20'
                      : 'text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                  title={t.deviceCard.disconnectWifi}
                >
                  {loading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <WifiOff className="w-3.5 h-3.5" />
                  )}
                </Button>
              )}

              {/* Disconnect All button */}
              {onDisconnectAll && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleDisconnectAllClick}
                  disabled={loading}
                  className="h-7 w-7 rounded-full text-slate-400 dark:text-slate-500 hover:text-orange-500 dark:hover:text-orange-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                  title={t.deviceCard.disconnectAll}
                >
                  {loading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Unplug className="w-3.5 h-3.5" />
                  )}
                </Button>
              )}

              {/* Delete button */}
              {onDelete && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleDeleteClick}
                  disabled={loading}
                  className="h-7 w-7 rounded-full text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                  title={t.deviceCard.deleteDevice}
                >
                  {loading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="w-3.5 h-3.5" />
                  )}
                </Button>
              )}
            </div>

            {/* Agent status badge - always visible but compact */}
            {agent ? (
              <Badge
                variant={
                  agent.state === 'idle'
                    ? 'success'
                    : agent.state === 'busy'
                      ? 'warning'
                      : agent.state === 'error'
                        ? 'destructive'
                        : 'secondary'
                }
                className={`text-[10px] px-1.5 py-0 h-5 ${
                  isActive
                    ? agent.state === 'idle'
                      ? 'bg-green-500/10 text-green-600 dark:text-green-400'
                      : agent.state === 'busy'
                        ? 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'
                        : agent.state === 'error'
                          ? 'bg-red-500/10 text-red-600 dark:text-red-400'
                          : 'bg-slate-500/10 text-slate-600 dark:text-slate-400'
                    : ''
                }`}
              >
                {agent.state === 'idle' && (
                  <CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />
                )}
                {agent.state === 'busy' && (
                  <Loader2 className="w-2.5 h-2.5 mr-0.5 animate-spin" />
                )}
                {agent.state === 'error' && (
                  <XCircle className="w-2.5 h-2.5 mr-0.5" />
                )}
                {agent.state === 'initializing' && (
                  <Clock className="w-2.5 h-2.5 mr-0.5" />
                )}
              </Badge>
            ) : null}
          </div>
        </div>
      </div>

      <ConfirmDialog
        isOpen={showWifiConfirm}
        title={t.deviceCard.connectWifiTitle}
        content={t.deviceCard.connectWifiContent}
        onConfirm={handleConfirmWifi}
        onCancel={() => setShowWifiConfirm(false)}
      />

      <ConfirmDialog
        isOpen={showDisconnectConfirm}
        title={t.deviceCard.disconnectWifiTitle}
        content={t.deviceCard.disconnectWifiContent}
        onConfirm={handleConfirmDisconnect}
        onCancel={() => setShowDisconnectConfirm(false)}
      />

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title={t.deviceCard.deleteDeviceTitle}
        content={t.deviceCard.deleteDeviceContent}
        onConfirm={handleConfirmDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />

      <ConfirmDialog
        isOpen={showDisconnectAllConfirm}
        title={t.deviceCard.disconnectAllTitle}
        content={t.deviceCard.disconnectAllContent}
        onConfirm={handleConfirmDisconnectAll}
        onCancel={() => setShowDisconnectAllConfirm(false)}
      />

      {/* Rename Dialog */}
      <Dialog open={showRenameDialog} onOpenChange={setShowRenameDialog}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>{t.deviceCard.renameDeviceTitle}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="device-alias">{t.deviceCard.deviceAlias}</Label>
              <Input
                id="device-alias"
                value={editValue}
                onChange={e => setEditValue(e.target.value)}
                placeholder={model || t.deviceCard.unknownDevice}
                autoFocus
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    handleSaveRename();
                  }
                }}
              />
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t.deviceCard.deviceAliasHint}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRenameDialog(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={handleSaveRename} disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              {t.common.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
