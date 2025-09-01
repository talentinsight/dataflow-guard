'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/hooks/use-toast'
import { apiClient } from '@/lib/api-client'
import { Plus, TestTube, Check, X, AlertCircle } from 'lucide-react'

interface Connection {
  name: string
  type: 'snowflake' | 'postgres' | 'bigquery' | 'redshift'
  account?: string
  username?: string
  password?: string
  database: string
  schema?: string
  warehouse?: string
  role?: string
  region?: string
  auth_method: string
  read_only: boolean
  enabled: boolean
}

export default function ConnectionsPage() {
  const [showForm, setShowForm] = useState(false)
  const [editingConnection, setEditingConnection] = useState<Connection | null>(null)
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: connections, isLoading } = useQuery({
    queryKey: ['connections'],
    queryFn: () => apiClient.getConnections(),
  })

  const createMutation = useMutation({
    mutationFn: (connection: Connection) => apiClient.createConnection(connection),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connections'] })
      setShowForm(false)
      setEditingConnection(null)
      toast({
        title: 'Success',
        description: 'Connection saved successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save connection',
        variant: 'destructive',
      })
    },
  })

  const testMutation = useMutation({
    mutationFn: (connection: Connection) => apiClient.testConnection(connection),
    onSuccess: (result) => {
      toast({
        title: result.status === 'success' ? 'Connection Test Passed' : 'Connection Test Failed',
        description: result.message,
        variant: result.status === 'success' ? 'default' : 'destructive',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Connection Test Failed',
        description: error.message || 'Failed to test connection',
        variant: 'destructive',
      })
    },
  })

  const handleSubmit = (connection: Connection) => {
    createMutation.mutate(connection)
  }

  const handleTest = (connection: Connection) => {
    testMutation.mutate(connection)
  }

  if (isLoading) {
    return <div>Loading connections...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Database Connections</h1>
          <p className="text-muted-foreground">
            Manage database connections for test execution
          </p>
        </div>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Connection
        </Button>
      </div>

      {/* Existing Connections */}
      <div className="grid gap-4">
        {connections?.map((connection: any) => (
          <Card key={connection.name}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {connection.name}
                    <Badge variant={connection.enabled ? 'default' : 'secondary'}>
                      {connection.enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                    <Badge variant="outline">{connection.type}</Badge>
                  </CardTitle>
                  <CardDescription>
                    {connection.type === 'snowflake' 
                      ? `${connection.account} • ${connection.database}.${connection.schema}`
                      : `${connection.host}:${connection.port} • ${connection.database}`
                    }
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTest(connection)}
                    disabled={testMutation.isPending}
                  >
                    <TestTube className="mr-2 h-4 w-4" />
                    Test
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditingConnection(connection)
                      setShowForm(true)
                    }}
                  >
                    Edit
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">User:</span> {connection.username}
                </div>
                <div>
                  <span className="font-medium">Auth:</span> {connection.auth_method}
                </div>
                {connection.type === 'snowflake' && (
                  <>
                    <div>
                      <span className="font-medium">Warehouse:</span> {connection.warehouse}
                    </div>
                    <div>
                      <span className="font-medium">Role:</span> {connection.role}
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Connection Form */}
      {showForm && (
        <ConnectionForm
          connection={editingConnection}
          onSubmit={handleSubmit}
          onCancel={() => {
            setShowForm(false)
            setEditingConnection(null)
          }}
          onTest={handleTest}
          isSubmitting={createMutation.isPending}
          isTesting={testMutation.isPending}
        />
      )}
    </div>
  )
}

interface ConnectionFormProps {
  connection?: Connection | null
  onSubmit: (connection: Connection) => void
  onCancel: () => void
  onTest: (connection: Connection) => void
  isSubmitting: boolean
  isTesting: boolean
}

function ConnectionForm({ 
  connection, 
  onSubmit, 
  onCancel, 
  onTest, 
  isSubmitting, 
  isTesting 
}: ConnectionFormProps) {
  const [formData, setFormData] = useState<Connection>(
    connection || {
      name: '',
      type: 'snowflake',
      account: '',
      username: '',
      password: '',
      database: '',
      schema: '',
      warehouse: '',
      role: '',
      region: '',
      auth_method: 'password',
      read_only: true,
      enabled: true,
    }
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleTest = () => {
    onTest(formData)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {connection ? 'Edit Connection' : 'Add New Connection'}
        </CardTitle>
        <CardDescription>
          Configure database connection settings. All connections are read-only by default.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Connection Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., snowflake_prod"
                required
              />
            </div>
            <div>
              <Label htmlFor="type">Database Type</Label>
              <Select
                value={formData.type}
                onValueChange={(value: any) => setFormData({ ...formData, type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="snowflake">Snowflake</SelectItem>
                  <SelectItem value="postgres">PostgreSQL</SelectItem>
                  <SelectItem value="bigquery">BigQuery</SelectItem>
                  <SelectItem value="redshift">Redshift</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Tabs value={formData.type} className="w-full">
            <TabsContent value="snowflake" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="account">Account</Label>
                  <Input
                    id="account"
                    value={formData.account || ''}
                    onChange={(e) => setFormData({ ...formData, account: e.target.value })}
                    placeholder="xy12345.eu-west-1"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="region">Region</Label>
                  <Input
                    id="region"
                    value={formData.region || ''}
                    onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                    placeholder="eu-west-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={formData.username || ''}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    placeholder="dfg_runner"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="auth_method">Auth Method</Label>
                  <Select
                    value={formData.auth_method}
                    onValueChange={(value) => setFormData({ ...formData, auth_method: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="password">Password</SelectItem>
                      <SelectItem value="private_key">Private Key</SelectItem>
                      <SelectItem value="iam">IAM</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {formData.auth_method === 'password' && (
                <div>
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password || ''}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Enter password"
                  />
                </div>
              )}

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="database">Database</Label>
                  <Input
                    id="database"
                    value={formData.database}
                    onChange={(e) => setFormData({ ...formData, database: e.target.value })}
                    placeholder="PROD_DB"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="schema">Schema</Label>
                  <Input
                    id="schema"
                    value={formData.schema || ''}
                    onChange={(e) => setFormData({ ...formData, schema: e.target.value })}
                    placeholder="RAW"
                  />
                </div>
                <div>
                  <Label htmlFor="warehouse">Warehouse</Label>
                  <Input
                    id="warehouse"
                    value={formData.warehouse || ''}
                    onChange={(e) => setFormData({ ...formData, warehouse: e.target.value })}
                    placeholder="ANALYTICS_WH"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="role">Role</Label>
                <Input
                  id="role"
                  value={formData.role || ''}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  placeholder="DFG_RO"
                />
              </div>
            </TabsContent>

            <TabsContent value="postgres" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="host">Host</Label>
                  <Input
                    id="host"
                    value={formData.host || ''}
                    onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                    placeholder="localhost"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="port">Port</Label>
                  <Input
                    id="port"
                    type="number"
                    value={formData.port || 5432}
                    onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
                    placeholder="5432"
                  />
                </div>
              </div>
              {/* Add more PostgreSQL-specific fields as needed */}
            </TabsContent>
          </Tabs>

          <div className="flex justify-between">
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={handleTest}
                disabled={isTesting}
              >
                <TestTube className="mr-2 h-4 w-4" />
                {isTesting ? 'Testing...' : 'Test Connection'}
              </Button>
            </div>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Connection'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
